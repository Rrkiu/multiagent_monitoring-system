"""
Vision Analysis Skill
이미지 기반 안전 분석 및 PPE 감지
"""

from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from PIL import Image

from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
from skills.base_skill import BaseSkill, SkillMetadata


class VisionAnalysisSkill(BaseSkill):
    """
    이미지 기반 안전 분석 Skill
    
    기능:
    - PPE(개인보호장비) 위반 감지
    - 작업장 안전 상태 평가
    - 다중 이미지 비교 분석
    - 개선 전후 비교
    """
    
    def _load_metadata(self) -> SkillMetadata:
        """메타데이터 로드"""
        return SkillMetadata(
            name="vision_analysis",
            description="이미지 기반 안전 분석 및 PPE 감지",
            version="1.0.0",
            author="Safety Team",
            dependencies=["PIL", "google-generativeai", "langchain-google-genai"],
            tags=["vision", "safety", "ppe", "analysis", "multimodal"]
        )
    
    def _initialize_tools(self) -> Dict[str, Any]:
        """도구 초기화"""
        # config가 아직 로드되지 않았을 수 있으므로 안전하게 접근
        config = getattr(self, 'config', {})
        
        # LLM 초기화
        llm = ChatGoogleGenerativeAI(
            model=config.get('vision_model', settings.vision_model),
            temperature=0.3,
            google_api_key=settings.google_api_key
        )
        
        return {
            'llm': llm,
            'image_processor': self._create_image_processor(),
            'ppe_detector': self._create_ppe_detector(),
            'safety_assessor': self._create_safety_assessor()
        }
    
    def _create_image_processor(self):
        """이미지 전처리 도구 생성"""
        from tools.vision_tools import prepare_image_for_gemini
        return prepare_image_for_gemini
    
    def _create_ppe_detector(self):
        """PPE 감지 도구 생성"""
        # 간단한 래퍼 함수
        def detect(image: Image.Image, llm, prompt: str) -> Dict:
            """PPE 감지 실행"""
            from langchain_core.messages import HumanMessage
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": image}
                ]
            )
            
            response = llm.invoke([message])
            return self._parse_ppe_response(response.content)
        
        return detect
    
    def _create_safety_assessor(self):
        """안전 평가 도구 생성"""
        def assess(image: Image.Image, llm, prompt: str) -> Dict:
            """안전 평가 실행"""
            from langchain_core.messages import HumanMessage
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": image}
                ]
            )
            
            response = llm.invoke([message])
            return self._parse_safety_response(response.content)
        
        return assess
    
    def execute(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Vision Analysis 실행
        
        Args:
            task: 수행할 작업
            context: 작업 컨텍스트
            
        Returns:
            작업 결과
        """
        if context is None:
            context = {}
        
        # Task 라우팅
        if task == "detect_ppe":
            return self._detect_ppe(context)
        elif task == "assess_safety":
            return self._assess_safety(context)
        elif task == "compare_images":
            return self._compare_images(context)
        elif task == "analyze_multiple":
            return self._analyze_multiple(context)
        elif task == "analyze_with_context":
            return self._analyze_with_context(context)
        else:
            raise ValueError(f"Unknown task: {task}")
    
    def _detect_ppe(self, context: Dict) -> Dict:
        """
        PPE 감지
        
        Args:
            context: {'image': str, 'camera_id': str (optional)}
            
        Returns:
            {'violations': [...], 'risk_level': str, 'recommendations': [...]}
        """
        # 이미지 준비
        image = self.tools['image_processor'](context['image'])
        
        # 프롬프트 가져오기
        prompt = self.get_prompt('ppe_detection')
        if not prompt:
            prompt = self._get_default_ppe_prompt()
        
        # PPE 감지 실행
        result = self.tools['ppe_detector'](
            image=image,
            llm=self.tools['llm'],
            prompt=prompt
        )
        
        # 위험도 계산
        risk_level = self._calculate_risk_level(result.get('violations', []))
        
        return {
            'violations': result.get('violations', []),
            'risk_level': risk_level,
            'recommendations': self._generate_recommendations(result.get('violations', [])),
            'camera_id': context.get('camera_id', 'unknown')
        }
    
    def _assess_safety(self, context: Dict) -> Dict:
        """
        안전 평가
        
        Args:
            context: {'image': str, 'context': str (optional)}
            
        Returns:
            {'overall_safety': str, 'hazards': [...], 'recommendations': [...]}
        """
        # 이미지 준비
        image = self.tools['image_processor'](context['image'])
        
        # 프롬프트 가져오기
        prompt = self.get_prompt('safety_assessment')
        if not prompt:
            prompt = self._get_default_safety_prompt()
        
        # 컨텍스트 추가
        if 'context' in context:
            prompt = f"{prompt}\n\n추가 컨텍스트: {context['context']}"
        
        # 안전 평가 실행
        result = self.tools['safety_assessor'](
            image=image,
            llm=self.tools['llm'],
            prompt=prompt
        )
        
        return result
    
    def _compare_images(self, context: Dict) -> Dict:
        """
        이미지 비교
        
        Args:
            context: {'before_image': str, 'after_image': str}
            
        Returns:
            {'changes': [...], 'improvement': bool, 'summary': str}
        """
        # 이미지 준비
        before_image = self.tools['image_processor'](context['before_image'])
        after_image = self.tools['image_processor'](context['after_image'])
        
        # 프롬프트 가져오기
        prompt = self.get_prompt('comparison')
        if not prompt:
            prompt = self._get_default_comparison_prompt()
        
        # 비교 분석 (간단한 구현)
        from langchain_core.messages import HumanMessage
        
        message = HumanMessage(
            content=[
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": before_image},
                {"type": "image_url", "image_url": after_image}
            ]
        )
        
        response = self.tools['llm'].invoke([message])
        
        return self._parse_comparison_response(response.content)
    
    def _analyze_multiple(self, context: Dict) -> Dict:
        """
        다중 이미지 분석
        
        Args:
            context: {'images': List[str], 'query': str}
            
        Returns:
            {'results': [...], 'summary': str}
        """
        images = context.get('images', [])
        query = context.get('query', '이미지들의 안전 상태를 분석해주세요')
        
        results = []
        
        for idx, image_path in enumerate(images):
            result = self._detect_ppe({'image': image_path})
            results.append({
                'image_index': idx,
                'image_path': image_path,
                'result': result
            })
        
        # 전체 요약
        summary = self._summarize_multiple_results(results)
        
        return {
            'results': results,
            'summary': summary,
            'total_images': len(images)
        }
    
    def _analyze_with_context(self, context: Dict) -> Dict:
        """
        컨텍스트 기반 분석
        
        Args:
            context: {'image': str, 'query': str, 'context': str}
            
        Returns:
            분석 결과
        """
        # 기본 분석 수행
        result = self._assess_safety(context)
        
        # 추가 컨텍스트 반영
        if 'context' in context:
            result['context_applied'] = context['context']
        
        return result
    
    def get_capabilities(self) -> List[str]:
        """Skill 기능 목록"""
        return [
            "detect_ppe",
            "assess_safety",
            "compare_images",
            "analyze_multiple",
            "analyze_with_context"
        ]
    
    def validate_input(self, task: str, context: Dict[str, Any]) -> bool:
        """입력 검증"""
        if task == "detect_ppe" or task == "assess_safety" or task == "analyze_with_context":
            return 'image' in context
        elif task == "compare_images":
            return 'before_image' in context and 'after_image' in context
        elif task == "analyze_multiple":
            return 'images' in context and isinstance(context['images'], list)
        return False
    
    # Helper methods
    
    def _calculate_risk_level(self, violations: List[Dict]) -> str:
        """위반 사항으로부터 위험도 계산"""
        if not violations:
            return 'low'
        
        high_severity_count = sum(1 for v in violations if v.get('severity') == 'high')
        
        if high_severity_count > 0:
            return 'high'
        elif len(violations) > 2:
            return 'medium'
        else:
            return 'low'
    
    def _generate_recommendations(self, violations: List[Dict]) -> List[str]:
        """위반 사항에 대한 권고사항 생성"""
        recommendations = []
        
        for violation in violations:
            v_type = violation.get('type', '')
            
            if 'helmet' in v_type:
                recommendations.append('안전모 착용 필수')
            elif 'vest' in v_type:
                recommendations.append('안전 조끼 착용 필수')
            elif 'shoes' in v_type:
                recommendations.append('안전화 착용 필수')
            elif 'gloves' in v_type:
                recommendations.append('보호 장갑 착용 필수')
        
        if len(violations) > 0:
            recommendations.append('작업 중단 및 안전 교육 실시 권고')
        
        return list(set(recommendations))  # 중복 제거
    
    def _summarize_multiple_results(self, results: List[Dict]) -> str:
        """다중 이미지 분석 결과 요약"""
        total = len(results)
        high_risk = sum(1 for r in results if r['result']['risk_level'] == 'high')
        medium_risk = sum(1 for r in results if r['result']['risk_level'] == 'medium')
        low_risk = sum(1 for r in results if r['result']['risk_level'] == 'low')
        
        return f"총 {total}개 이미지 분석 완료. 고위험: {high_risk}, 중위험: {medium_risk}, 저위험: {low_risk}"
    
    def _parse_ppe_response(self, response: str) -> Dict:
        """PPE 감지 응답 파싱"""
        # 간단한 파싱 (실제로는 더 정교한 파싱 필요)
        violations = []
        
        if '안전모' in response and ('미착용' in response or '없음' in response):
            violations.append({
                'type': 'helmet_missing',
                'severity': 'high',
                'confidence': 0.9
            })
        
        if '조끼' in response and ('미착용' in response or '없음' in response):
            violations.append({
                'type': 'vest_missing',
                'severity': 'medium',
                'confidence': 0.85
            })
        
        return {'violations': violations}
    
    def _parse_safety_response(self, response: str) -> Dict:
        """안전 평가 응답 파싱"""
        # 간단한 파싱
        return {
            'overall_safety': 'medium',
            'hazards': [],
            'recommendations': [],
            'raw_response': response
        }
    
    def _parse_comparison_response(self, response: str) -> Dict:
        """비교 분석 응답 파싱"""
        return {
            'changes': [],
            'improvement': True,
            'summary': response
        }
    
    # Default prompts
    
    def _get_default_ppe_prompt(self) -> str:
        """기본 PPE 감지 프롬프트"""
        return """이 이미지에서 작업자의 개인보호장비(PPE) 착용 상태를 분석해주세요.

확인 항목:
1. 안전모 착용 여부
2. 안전 조끼 착용 여부
3. 안전화 착용 여부
4. 보호 장갑 착용 여부

각 항목에 대해 착용 여부와 위반 사항을 명확히 기술해주세요."""
    
    def _get_default_safety_prompt(self) -> str:
        """기본 안전 평가 프롬프트"""
        return """이 작업장의 전반적인 안전 상태를 평가해주세요.

평가 항목:
1. PPE 착용 상태
2. 작업 환경의 위험 요소
3. 안전 시설 및 장비 상태
4. 작업자의 안전한 작업 자세

위험도를 평가하고 개선 권고사항을 제시해주세요."""
    
    def _get_default_comparison_prompt(self) -> str:
        """기본 비교 분석 프롬프트"""
        return """두 이미지를 비교하여 안전 상태의 변화를 분석해주세요.

첫 번째 이미지: 개선 전
두 번째 이미지: 개선 후

변화 사항과 개선 효과를 상세히 기술해주세요."""
