"""
웹 검색 도구 모듈
DuckDuckGo Rate Limit 문제 해결을 위한 개선된 구현
"""

from langchain.tools import Tool
from typing import Optional, List, Dict
import json
import time
import random
import requests
from urllib.parse import quote_plus


class ImprovedDuckDuckGoSearch:
    """
    개선된 DuckDuckGo 검색 클래스
    Rate Limit 문제를 최소화하기 위한 직접 HTTP 요청 방식
    """
    
    def __init__(self, max_results: int = 3, timeout: int = 10):
        self.max_results = max_results
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
        })
    
    def search(self, query: str) -> str:
        """
        DuckDuckGo 검색 수행 (HTML 스크래핑 방식)
        
        Args:
            query: 검색 쿼리
            
        Returns:
            str: 검색 결과 텍스트
        """
        try:
            # DuckDuckGo HTML 검색 URL
            encoded_query = quote_plus(query)
            url = f"https://html.duckduckgo.com/html/?q={encoded_query}"
            
            # 요청 전 짧은 딜레이
            time.sleep(random.uniform(1, 2))
            
            response = self.session.get(url, timeout=self.timeout)
            
            if response.status_code == 200:
                # 간단한 텍스트 추출 (BeautifulSoup 없이)
                text = response.text
                
                # 결과 추출 (간단한 파싱)
                results = []
                snippets = text.split('result__snippet')
                
                for i, snippet in enumerate(snippets[1:self.max_results+1], 1):
                    # 간단한 텍스트 추출
                    try:
                        # snippet에서 텍스트 부분만 추출
                        start = snippet.find('>') + 1
                        end = snippet.find('</a>')
                        if start > 0 and end > 0:
                            result_text = snippet[start:end]
                            # HTML 태그 제거
                            result_text = result_text.replace('<b>', '').replace('</b>', '')
                            result_text = result_text.strip()
                            if result_text:
                                results.append(f"{i}. {result_text}")
                    except:
                        continue
                
                if results:
                    return "\n\n".join(results)
                else:
                    return "검색 결과를 찾을 수 없습니다."
            else:
                return f"검색 실패: HTTP {response.status_code}"
                
        except requests.exceptions.Timeout:
            return "검색 시간 초과. 잠시 후 다시 시도해주세요."
        except requests.exceptions.RequestException as e:
            return f"검색 중 네트워크 오류 발생: {str(e)}"
        except Exception as e:
            return f"검색 중 오류 발생: {str(e)}"


def safe_search_with_retry(search_func, query: str, max_retries: int = 2) -> str:
    """
    재시도 로직이 포함된 안전한 검색 함수
    
    Args:
        search_func: 검색 함수
        query: 검색 쿼리
        max_retries: 최대 재시도 횟수
        
    Returns:
        str: 검색 결과 또는 대체 메시지
    """
    for attempt in range(max_retries):
        try:
            # 요청 간 딜레이
            if attempt > 0:
                delay = random.uniform(3, 6) * (attempt + 1)
                print(f"⏳ 재시도 대기 중... {delay:.1f}초 ({attempt + 1}/{max_retries})")
                time.sleep(delay)
            
            result = search_func(query)
            
            # Rate Limit 메시지 확인
            if "rate" in result.lower() or "limit" in result.lower():
                if attempt < max_retries - 1:
                    continue
            
            return result
            
        except Exception as e:
            error_msg = str(e)
            
            if "Ratelimit" in error_msg or "rate" in error_msg.lower():
                if attempt < max_retries - 1:
                    continue
                else:
                    return generate_fallback_message(query)
            else:
                return f"검색 중 오류 발생: {error_msg}"
    
    return generate_fallback_message(query)


def generate_fallback_message(query: str) -> str:
    """
    웹 검색 실패 시 대체 메시지 생성
    
    Args:
        query: 검색 쿼리
        
    Returns:
        str: 대체 메시지
    """
    return f"""
⚠️ 웹 검색 서비스가 일시적으로 사용 불가능합니다.

검색하려던 내용: "{query}"

현재 DuckDuckGo 검색 서비스의 요청 제한으로 인해 검색을 수행할 수 없습니다.

📋 대안:
1. **내부 지식 베이스 활용**: 시스템 내부의 안전 관련 문서와 규정을 검색합니다.
2. **구체적인 질문**: 내부 데이터베이스에 있는 정보로 답변 가능한 질문을 해주세요.
3. **나중에 재시도**: 1-2분 후 다시 시도해주세요.

💡 추천 질문:
- "우리 작업장의 안전 이벤트 현황은?"
- "최근 7일간 위험도 평가 결과는?"
- "안전모 미착용 이벤트에 대한 조치 방안은?"

참고: 이 문제는 외부 검색 서비스의 일시적인 제한이며, 내부 데이터 조회 및 분석 기능은 정상적으로 작동합니다.
"""


def create_web_search_tool() -> Tool:
    """
    개선된 웹 검색 도구 생성
    
    Returns:
        Tool: 웹 검색 도구
    """
    searcher = ImprovedDuckDuckGoSearch(max_results=3, timeout=10)
    
    def search_with_retry(query: str) -> str:
        return safe_search_with_retry(searcher.search, query, max_retries=2)
    
    return Tool(
        name="web_search",
        description="""
        웹에서 정보를 검색합니다. 
        최신 정보, 뉴스, 안전 규정, 기술 문서 등을 찾을 때 사용하세요.
        
        ⚠️ 주의: 외부 검색 서비스 제한으로 인해 항상 사용 가능하지 않을 수 있습니다.
        검색 실패 시 내부 지식 베이스를 활용하는 것을 권장합니다.
        
        입력: 검색할 키워드나 질문 (한국어 또는 영어)
        출력: 검색 결과 요약 또는 대체 안내
        """,
        func=search_with_retry
    )


def create_detailed_web_search_tool() -> Tool:
    """
    상세 웹 검색 도구 생성
    
    Returns:
        Tool: 상세 웹 검색 도구
    """
    searcher = ImprovedDuckDuckGoSearch(max_results=5, timeout=15)
    
    def search_with_retry(query: str) -> str:
        return safe_search_with_retry(searcher.search, query, max_retries=2)
    
    return Tool(
        name="detailed_web_search",
        description="""
        웹에서 상세한 정보를 검색합니다 (최대 5개 결과).
        심층적인 조사나 여러 출처의 정보가 필요할 때 사용하세요.
        
        ⚠️ 주의: 외부 검색 서비스 제한으로 인해 항상 사용 가능하지 않을 수 있습니다.
        """,
        func=search_with_retry
    )


def search_safety_news(query: str) -> str:
    """
    안전 관련 최신 뉴스 검색
    
    Args:
        query: 검색 쿼리
        
    Returns:
        str: 검색 결과
    """
    enhanced_query = f"{query} 안전 뉴스 최신"
    searcher = ImprovedDuckDuckGoSearch(max_results=3, timeout=10)
    return safe_search_with_retry(searcher.search, enhanced_query, max_retries=2)


def search_safety_regulations(query: str) -> str:
    """
    안전 규정 및 법규 검색
    
    Args:
        query: 검색 쿼리
        
    Returns:
        str: 검색 결과
    """
    enhanced_query = f"{query} 산업안전보건법 규정"
    searcher = ImprovedDuckDuckGoSearch(max_results=3, timeout=10)
    return safe_search_with_retry(searcher.search, enhanced_query, max_retries=2)


def create_safety_news_tool() -> Tool:
    """안전 뉴스 검색 도구 생성"""
    return Tool(
        name="search_safety_news",
        description="""
        안전 관련 최신 뉴스를 검색합니다.
        산업재해, 안전사고, 안전 정책 등의 최신 소식을 찾을 때 사용하세요.
        
        ⚠️ 외부 검색 서비스 제한으로 인해 항상 사용 가능하지 않을 수 있습니다.
        """,
        func=search_safety_news
    )


def create_safety_regulations_tool() -> Tool:
    """안전 규정 검색 도구 생성"""
    return Tool(
        name="search_safety_regulations",
        description="""
        안전 규정 및 법규를 검색합니다.
        산업안전보건법, OSHA 규정, 안전 가이드라인 등을 찾을 때 사용하세요.
        
        ⚠️ 외부 검색 서비스 제한으로 인해 항상 사용 가능하지 않을 수 있습니다.
        """,
        func=search_safety_regulations
    )


# 모든 웹 검색 도구를 리스트로 제공
def get_all_web_search_tools():
    """모든 웹 검색 도구 반환"""
    return [
        create_web_search_tool(),
        create_detailed_web_search_tool(),
        create_safety_news_tool(),
        create_safety_regulations_tool()
    ]
