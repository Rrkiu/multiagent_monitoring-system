"""
Response Formatter
Skills의 원시 응답을 사용자 친화적인 형태로 변환
"""

from typing import Dict, Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
import json


class ResponseFormatter:
    """응답 포맷터 - Skills 결과를 사용자 친화적으로 변환"""
    
    def __init__(self):
        """포맷터 초기화"""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0.3,
            google_api_key=settings.google_api_key,
            timeout=60,  # 60초 타임아웃
            max_retries=3  # 최대 3회 재시도
        )
    
    def format_response(
        self, 
        raw_result: Any, 
        user_query: str,
        skill_name: str,
        task: str
    ) -> str:
        """
        원시 결과를 사용자 친화적인 응답으로 변환
        
        Args:
            raw_result: Skill의 원시 결과
            user_query: 사용자 원래 질문
            skill_name: 실행된 Skill 이름
            task: 실행된 task 이름
            
        Returns:
            사용자 친화적인 응답 문자열
        """
        
        # 1. 이미 문자열이고 충분히 친화적인 경우
        if isinstance(raw_result, str) and self._is_user_friendly(raw_result):
            return raw_result
        
        # 2. Dict 결과 처리
        if isinstance(raw_result, dict):
            # 특정 키가 있는 경우 직접 추출
            friendly_result = self._extract_friendly_content(raw_result)
            if friendly_result:
                return friendly_result
            
            # LLM으로 포맷팅
            return self._format_with_llm(raw_result, user_query, skill_name, task)
        
        # 3. 기타 타입
        return str(raw_result)
    
    def _is_user_friendly(self, text: str) -> bool:
        """텍스트가 사용자 친화적인지 확인"""
        
        # 비친화적 패턴
        unfriendly_patterns = [
            '"content":',
            '"metadata":',
            '"event_type":',
            '"source":',
            'page_content',
            '{"',
            '[{',
        ]
        
        # 비친화적 패턴이 있으면 False
        for pattern in unfriendly_patterns:
            if pattern in text[:100]:  # 첫 100자만 체크
                return False
        
        return True
    
    def _extract_friendly_content(self, result: Dict) -> Optional[str]:
        """Dict에서 사용자 친화적인 콘텐츠 추출"""
        
        # 우선순위 순서대로 키 확인
        priority_keys = [
            'answer',           # knowledge_management
            'action_plan',      # report_generation
            'report',           # report_generation
            'summary',          # report_generation
            'guide',            # knowledge_management
            'content',          # 일반
            'response',         # 일반
            'message',          # 일반
        ]
        
        for key in priority_keys:
            if key in result:
                content = result[key]
                if isinstance(content, str) and len(content) > 10:
                    # 마크다운 포맷팅 제거 후 반환
                    return self._remove_markdown(content)
        
        # results 배열 처리
        if 'results' in result:
            results = result['results']
            if isinstance(results, list) and len(results) > 0:
                first = results[0]
                if isinstance(first, dict):
                    content = first.get('content', '')
                    return self._remove_markdown(content)
                elif hasattr(first, 'page_content'):
                    return self._remove_markdown(first.page_content)
        
        return None
    
    def _remove_markdown(self, text: str) -> str:
        """마크다운 포맷팅 제거"""
        import re
        
        # 1. 헤딩 제거 (# ## ### 등)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # 2. 볼드 제거 (**text** -> text)
        # 개선: 이모지, 특수문자, 공백 모두 포함
        text = re.sub(r'\*\*([^\*]+?)\*\*', r'\1', text)
        
        # 3. 이탤릭 제거 (*text* -> text)
        # 볼드가 아닌 단일 * 제거
        text = re.sub(r'(?<!\*)\*([^\*]+?)\*(?!\*)', r'\1', text)
        
        # 4. 코드 블록 제거 (```)
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        
        # 5. 링크 포맷 제거 ([text](url) -> text)
        text = re.sub(r'\[(.+?)\]\(.+?\)', r'\1', text)
        
        return text.strip()
    
    def _format_with_llm(
        self, 
        raw_result: Dict, 
        user_query: str,
        skill_name: str,
        task: str
    ) -> str:
        """LLM을 사용하여 응답 포맷팅"""
        
        # 결과를 JSON 문자열로 변환
        result_json = json.dumps(raw_result, ensure_ascii=False, indent=2)
        
        prompt = f"""당신은 안전 모니터링 시스템의 응답 생성 전문가입니다.

사용자 질문: {user_query}

시스템이 생성한 원시 데이터:
{result_json}

위 데이터를 바탕으로 사용자에게 친화적이고 이해하기 쉬운 답변을 작성해주세요.

작성 지침:
1. 사용자 질문에 직접적으로 답변
2. 기술적인 용어나 JSON 형식 제거
3. 명확하고 구조화된 형식 사용
4. 이모지 적절히 활용 (📊, ⚠️, ✅ 등)
5. 핵심 정보를 강조
6. 한국어로 작성
7. 메타데이터나 시스템 정보는 제외
8. 마크다운 포맷팅 사용 금지:
   - ** (볼드) 사용 금지
   - * (이탤릭) 사용 금지
   - # (헤딩) 사용 금지
   - 대신 줄바꿈과 이모지로 구조화
   - 숫자 목록(1. 2. 3.)과 불릿(•)은 사용 가능

답변:"""

        try:
            response = self.llm.invoke(prompt)
            return response.content
        except Exception as e:
            # LLM 실패 시 기본 포맷팅
            return self._fallback_format(raw_result)
    
    def _fallback_format(self, result: Dict) -> str:
        """LLM 실패 시 기본 포맷팅"""
        
        # 간단한 텍스트 변환
        formatted = []
        
        for key, value in result.items():
            # 메타데이터 키 제외
            if key in ['metadata', 'source', 'source_file', 'event_type']:
                continue
            
            if isinstance(value, (str, int, float)):
                formatted.append(f"{key}: {value}")
            elif isinstance(value, dict):
                formatted.append(f"{key}:")
                for k, v in value.items():
                    formatted.append(f"  - {k}: {v}")
        
        return "\n".join(formatted) if formatted else json.dumps(result, ensure_ascii=False, indent=2)


# 싱글톤 인스턴스
_formatter_instance = None

def get_formatter() -> ResponseFormatter:
    """포맷터 싱글톤 반환"""
    global _formatter_instance
    if _formatter_instance is None:
        _formatter_instance = ResponseFormatter()
    return _formatter_instance
