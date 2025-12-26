"""
웹 검색 에이전트
필요한 정보를 웹에서 검색하고 요약하는 전문 에이전트
"""

from langchain.agents import AgentExecutor, create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from typing import Optional

from config import settings
from tools.web_search_tools import get_all_web_search_tools


class SearchAgent:
    """
    웹 검색 전담 에이전트
    
    역할:
    - 웹에서 최신 정보 검색
    - 안전 규정 및 법규 조회
    - 안전 관련 뉴스 수집
    - 기술 문서 및 가이드라인 검색
    """
    
    def __init__(self):
        """SearchAgent 초기화"""
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0.5,  # 적절한 창의성과 정확성 균형
            google_api_key=settings.google_api_key
        )
        
        # 웹 검색 도구들
        self.tools = get_all_web_search_tools()
        
        # ReAct 프롬프트 템플릿
        self.prompt = PromptTemplate.from_template(
            """당신은 웹 검색 전문가입니다.
사용자의 질문에 답하기 위해 웹에서 정보를 검색하고 요약합니다.

사용 가능한 도구:
{tools}

도구 이름: {tool_names}

다음 형식을 엄격히 따르세요:

Question: 답변해야 할 입력 질문
Thought: 무엇을 해야 할지 생각합니다
Action: 수행할 작업, 반드시 [{tool_names}] 중 하나여야 합니다
Action Input: 작업에 대한 입력
Observation: 작업의 결과
... (이 Thought/Action/Action Input/Observation을 여러 번 반복할 수 있습니다)
Thought: 이제 최종 답변을 알았습니다
Final Answer: 원래 입력 질문에 대한 최종 답변

중요 지침:
1. 검색 결과를 명확하고 간결하게 요약하세요
2. 출처가 있다면 함께 제공하세요
3. 최신 정보인지 확인하세요
4. 여러 검색 결과를 종합하여 답변하세요
5. 한국어로 답변하되, 필요시 영어 검색도 활용하세요

Question: {input}
Thought: {agent_scratchpad}"""
        )
        
        # ReAct 에이전트 생성
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )
        
        # AgentExecutor 생성
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=6,  # 웹 검색은 여러 단계가 필요할 수 있음
            handle_parsing_errors=True,
            return_intermediate_steps=False
        )
    
    def search(self, user_input: str) -> str:
        """
        웹 검색 수행
        
        Args:
            user_input: 사용자 검색 요청
            
        Returns:
            str: 검색 결과 요약
        """
        try:
            print(f"\n[SearchAgent] 웹 검색 시작: {user_input}")
            
            # 에이전트 실행
            result = self.agent_executor.invoke({
                "input": user_input
            })
            
            # 결과 추출
            if isinstance(result, dict) and "output" in result:
                response = result["output"]
            else:
                response = str(result)
            
            print(f"[SearchAgent] 검색 완료")
            return response
            
        except Exception as e:
            error_msg = f"웹 검색 중 오류 발생: {str(e)}"
            print(f"[SearchAgent] 오류: {error_msg}")
            return error_msg
    
    def search_with_context(self, query: str, context: Optional[str] = None) -> str:
        """
        컨텍스트를 고려한 웹 검색
        
        Args:
            query: 검색 쿼리
            context: 추가 컨텍스트 정보
            
        Returns:
            str: 검색 결과
        """
        if context:
            enhanced_query = f"{query}\n\n추가 컨텍스트: {context}"
        else:
            enhanced_query = query
        
        return self.search(enhanced_query)


# 테스트 코드
if __name__ == "__main__":
    # SearchAgent 테스트
    agent = SearchAgent()
    
    # 테스트 쿼리들
    test_queries = [
        "산업안전보건법 최신 개정 내용",
        "작업장 안전모 착용 규정",
        "추락 방지 안전 가이드라인"
    ]
    
    print("=" * 60)
    print("SearchAgent 테스트 시작")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\n질문: {query}")
        print("-" * 60)
        
        response = agent.search(query)
        print(f"\n답변:\n{response}")
        print("=" * 60)
