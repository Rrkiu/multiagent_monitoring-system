"""
Multimodal Agent
이미지와 텍스트를 동시에 처리하는 멀티모달 에이전트
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from typing import List, Union, Optional, Dict, Any
from PIL import Image
import json

from config import settings
from tools.vision_tools import (
    prepare_image_for_gemini,
    process_multiple_images,
    image_to_base64
)


class MultimodalAgent:
    """
    멀티모달 에이전트
    
    역할:
    - 이미지 분석 (안전모 착용, 작업자 자세, 위험 상황 감지)
    - 이미지 + 텍스트 동시 처리
    - CCTV 스냅샷 분석
    - 시각적 안전 점검 보고서 생성
    - 이미지 기반 질의응답
    """
    
    def __init__(self):
        """Multimodal Agent 초기화"""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.vision_model,
            temperature=0.3,  # 이미지 분석은 정확성이 중요
            google_api_key=settings.google_api_key
        )
        
        # 안전 점검 프롬프트 템플릿
        self.safety_inspection_prompt = """당신은 산업 안전 전문가입니다.
제공된 이미지를 분석하여 안전 위반 사항과 위험 요소를 식별하세요.

다음 항목들을 중점적으로 확인하세요:

1. 개인 보호 장비 (PPE) 착용 여부
   - 안전모 (헬멧)
   - 안전복 (작업복)
   - 안전화
   - 보안경
   - 안전 장갑
   
2. 작업 환경 안전
   - 위험 구역 표시
   - 안전 펜스 및 차단막
   - 비상구 표시
   - 소화기 위치
   
3. 작업자 행동
   - 위험한 자세
   - 위험 구역 침입
   - 부적절한 장비 사용
   
4. 전반적인 위험도 평가
   - LOW: 경미한 위반 또는 개선 권장 사항
   - MEDIUM: 주의가 필요한 위반 사항
   - HIGH: 즉각적인 조치가 필요한 심각한 위험

다음 형식으로 응답해주세요:

## 감지된 위반 사항
- [위반 사항 1]: 설명 (위험도: LOW/MEDIUM/HIGH)
- [위반 사항 2]: 설명 (위험도: LOW/MEDIUM/HIGH)

## 작업자 수
- 감지된 작업자: X명

## 전반적인 위험도
- 위험도: LOW/MEDIUM/HIGH

## 권장 조치 사항
1. 권장 사항 1
2. 권장 사항 2

## 요약
전체 상황에 대한 간단한 요약

사용자 질문: {query}
"""
    
    def analyze_image(
        self,
        image_source: Union[str, Image.Image],
        query: str = "이 이미지의 안전 상태를 분석해주세요"
    ) -> str:
        """
        단일 이미지 분석
        
        Args:
            image_source: 이미지 경로, URL, 또는 PIL Image 객체
            query: 사용자 질문
            
        Returns:
            분석 결과
        """
        try:
            print(f"\n[MultimodalAgent] 이미지 분석 시작")
            print(f"[MultimodalAgent] 질문: {query}")
            
            # 이미지 전처리
            image = prepare_image_for_gemini(image_source)
            print(f"[MultimodalAgent] 이미지 크기: {image.size}")
            
            # 프롬프트 생성
            prompt = self.safety_inspection_prompt.format(query=query)
            
            # Gemini Vision API 호출
            # LangChain Google GenAI는 이미지를 직접 지원
            from langchain_core.messages import HumanMessage
            
            # 이미지를 base64로 인코딩
            image_base64 = image_to_base64(image, format="JPEG")
            
            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/jpeg;base64,{image_base64}"
                    }
                ]
            )
            
            # LLM 호출
            response = self.llm.invoke([message])
            result = response.content
            
            print(f"[MultimodalAgent] 분석 완료")
            return result
            
        except Exception as e:
            error_msg = f"이미지 분석 중 오류 발생: {str(e)}"
            print(f"[MultimodalAgent] 오류: {error_msg}")
            return error_msg
    
    def analyze_multiple_images(
        self,
        image_sources: List[Union[str, Image.Image]],
        query: str = "이 이미지들의 안전 상태를 비교 분석해주세요"
    ) -> str:
        """
        여러 이미지 동시 분석
        
        Args:
            image_sources: 이미지 소스 리스트
            query: 사용자 질문
            
        Returns:
            분석 결과
        """
        try:
            print(f"\n[MultimodalAgent] 다중 이미지 분석 시작")
            print(f"[MultimodalAgent] 이미지 개수: {len(image_sources)}")
            print(f"[MultimodalAgent] 질문: {query}")
            
            # 이미지들 전처리
            images = process_multiple_images(image_sources)
            
            if not images:
                return "처리 가능한 이미지가 없습니다."
            
            print(f"[MultimodalAgent] 처리된 이미지 개수: {len(images)}")
            
            # 프롬프트 생성
            prompt = f"""당신은 산업 안전 전문가입니다.
제공된 {len(images)}개의 이미지를 분석하여 비교하세요.

각 이미지별로:
1. 안전 상태 평가
2. 위반 사항 식별
3. 위험도 평가

그리고 전체적으로:
1. 공통된 문제점
2. 가장 위험한 구역
3. 개선이 필요한 우선순위

사용자 질문: {query}
"""
            
            # 메시지 구성
            from langchain_core.messages import HumanMessage
            
            content = [{"type": "text", "text": prompt}]
            
            # 각 이미지를 base64로 인코딩하여 추가
            for idx, image in enumerate(images):
                image_base64 = image_to_base64(image, format="JPEG")
                content.append({
                    "type": "image_url",
                    "image_url": f"data:image/jpeg;base64,{image_base64}"
                })
            
            message = HumanMessage(content=content)
            
            # LLM 호출
            response = self.llm.invoke([message])
            result = response.content
            
            print(f"[MultimodalAgent] 다중 이미지 분석 완료")
            return result
            
        except Exception as e:
            error_msg = f"다중 이미지 분석 중 오류 발생: {str(e)}"
            print(f"[MultimodalAgent] 오류: {error_msg}")
            return error_msg
    
    def analyze_with_context(
        self,
        image_source: Union[str, Image.Image],
        query: str,
        context: Optional[str] = None
    ) -> str:
        """
        컨텍스트를 고려한 이미지 분석
        
        Args:
            image_source: 이미지 소스
            query: 사용자 질문
            context: 추가 컨텍스트 정보 (예: 과거 이벤트 데이터)
            
        Returns:
            분석 결과
        """
        enhanced_query = query
        
        if context:
            enhanced_query = f"""{query}

추가 컨텍스트 정보:
{context}

위 컨텍스트를 고려하여 이미지를 분석하고, 과거 데이터와 비교하여 개선 여부를 평가해주세요.
"""
        
        return self.analyze_image(image_source, enhanced_query)
    
    def detect_ppe_violations(
        self,
        image_source: Union[str, Image.Image]
    ) -> str:
        """
        개인 보호 장비(PPE) 위반 사항 감지
        
        Args:
            image_source: 이미지 소스
            
        Returns:
            PPE 위반 사항 분석 결과
        """
        query = """이미지에서 개인 보호 장비(PPE) 착용 상태를 상세히 분석해주세요.

다음 항목들을 확인하세요:
1. 안전모 (헬멧) 착용 여부
2. 안전복 착용 여부
3. 안전화 착용 여부
4. 보안경 착용 여부
5. 안전 장갑 착용 여부

각 작업자별로 착용 상태를 평가하고, 미착용자가 있다면 명확히 지적해주세요.

다음 형식으로 응답해주세요:

## 전체 작업자 수
- 총 X명

## 작업자별 PPE 착용 상태
### 작업자 1
- 안전모: ✓/✗
- 안전복: ✓/✗
- 안전화: ✓/✗
- 보안경: ✓/✗
- 장갑: ✓/✗
- 위반 사항: [미착용 항목 나열]

### 작업자 2
...

## 전체 요약
전반적인 PPE 착용 상태 요약

## 즉각 조치 사항
1. 조치 사항 1
2. 조치 사항 2
"""
        return self.analyze_image(image_source, query)
    
    def assess_workplace_safety(
        self,
        image_source: Union[str, Image.Image]
    ) -> str:
        """
        작업장 전반적인 안전 상태 평가
        
        Args:
            image_source: 이미지 소스
            
        Returns:
            작업장 안전 평가 결과
        """
        query = """이 작업장의 전반적인 안전 상태를 종합적으로 평가해주세요.

평가 항목:
1. 작업 환경 정리정돈 상태
2. 안전 표지판 및 경고 표시
3. 비상구 및 대피로 확보
4. 소화기 및 안전 장비 배치
5. 위험 구역 표시 및 차단
6. 조명 및 가시성
7. 전반적인 위험도

각 항목을 평가하고 개선이 필요한 부분을 구체적으로 제시해주세요.
"""
        return self.analyze_image(image_source, query)
    
    def compare_before_after(
        self,
        before_image: Union[str, Image.Image],
        after_image: Union[str, Image.Image]
    ) -> str:
        """
        개선 전후 비교 분석
        
        Args:
            before_image: 개선 전 이미지
            after_image: 개선 후 이미지
            
        Returns:
            비교 분석 결과
        """
        query = """첫 번째 이미지(개선 전)와 두 번째 이미지(개선 후)를 비교 분석해주세요.

비교 항목:
1. 개선된 점
2. 여전히 문제가 있는 부분
3. 새로 발생한 문제
4. 전반적인 개선도 평가 (0-100%)
5. 추가 개선 권장 사항

구체적이고 명확하게 비교하여 설명해주세요.
"""
        return self.analyze_multiple_images([before_image, after_image], query)


# 테스트 코드
if __name__ == "__main__":
    print("=" * 60)
    print("Multimodal Agent 테스트")
    print("=" * 60)
    
    agent = MultimodalAgent()
    
    # 테스트용 이미지 경로 (실제 이미지로 교체 필요)
    test_image_path = "./data/test_image.jpg"
    
    # 이미지가 존재하는 경우에만 테스트
    from pathlib import Path
    if Path(test_image_path).exists():
        print("\n[테스트 1] 단일 이미지 안전 분석")
        print("-" * 60)
        result = agent.analyze_image(test_image_path)
        print(f"결과:\n{result}")
        print("=" * 60)
        
        print("\n[테스트 2] PPE 위반 감지")
        print("-" * 60)
        result = agent.detect_ppe_violations(test_image_path)
        print(f"결과:\n{result}")
        print("=" * 60)
        
        print("\n[테스트 3] 작업장 안전 평가")
        print("-" * 60)
        result = agent.assess_workplace_safety(test_image_path)
        print(f"결과:\n{result}")
        print("=" * 60)
    else:
        print(f"\n테스트 이미지가 없습니다: {test_image_path}")
        print("실제 이미지로 테스트하려면 이미지 파일을 준비해주세요.")
    
    print("\n✅ Multimodal Agent 테스트 완료")
