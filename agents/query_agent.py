"""
Query Agent
데이터 조회 및 검색을 전담하는 에이전트
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferMemory

from config import settings
from tools.data_tools import (
    get_camera_events,
    get_all_cameras,
    get_events_by_type,
    get_events_by_date,
    get_unresolved_events
)
from tools.rag_tools import search_knowledge_base


class QueryAgent:
    """조회 전담 에이전트"""

    def __init__(self):
        """Query Agent 초기화"""

        # LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=settings.llm_temperature,
            google_api_key=settings.google_api_key
        )

        # 이 에이전트가 사용할 도구들
        self.tools = [
            get_camera_events,
            get_all_cameras,
            get_events_by_type,
            get_events_by_date,
            get_unresolved_events,
            search_knowledge_base,
        ]

        # ReAct 프롬프트 템플릿
        template = """당신은 안전 모니터링 시스템의 데이터 조회 전문가입니다.

                    역할:
                    - 사용자의 요청에 따라 적절한 데이터를 조회합니다
                    - 카메라별, 날짜별, 이벤트 타입별로 데이터를 검색할 수 있습니다
                    - 필요한 경우 지식 베이스에서 관련 정보를 찾습니다
                    
                    지침:
                    1. 사용자의 요청을 정확히 파악하세요
                    2. 적절한 도구를 선택하여 데이터를 조회하세요
                    3. 조회된 데이터를 명확하고 간결하게 정리하여 제시하세요
                    4. 날짜는 'YYYY-MM-DD' 형식으로 사용하거나 'today', 'yesterday'를 사용할 수 있습니다
                    5. 데이터가 없는 경우 그 사실을 명확히 알려주세요
                    
                    사용 가능한 도구들:
                    {tools}
                    
                    도구 이름들: {tool_names}
                    
                    다음 형식을 사용하세요:
                    
                    Question: 답변해야 할 입력 질문
                    Thought: 무엇을 해야 할지 항상 생각해야 합니다
                    Action: 수행할 작업, [{tool_names}] 중 하나여야 합니다
                    Action Input: 작업에 대한 입력
                    Observation: 작업의 결과
                    ... (이 Thought/Action/Action Input/Observation을 여러 번 반복할 수 있습니다)
                    Thought: 이제 최종 답변을 알았습니다
                    Final Answer: 원래 입력 질문에 대한 최종 답변
                    
                    시작하세요!
                    
                    Question: {input}
                    Thought: {agent_scratchpad}"""

        self.prompt = PromptTemplate.from_template(template)

        # 에이전트 생성
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.prompt
        )

        # 에이전트 실행기
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )

    def query(self, user_input: str) -> str:
        """
        사용자 쿼리 처리

        Args:
            user_input: 사용자 입력

        Returns:
            에이전트 응답
        """
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return result.get("output", "응답을 생성할 수 없습니다.")
        except StopIteration:
            return "응답 생성 중 오류가 발생했습니다. 질문을 다시 입력해주세요."
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"쿼리 처리 중 오류가 발생했습니다: {str(e)}"


def main():
    """테스트용 메인 함수"""
    print("="*60)
    print("Query Agent 테스트")
    print("="*60)

    agent = QueryAgent()

    test_queries = [
        "CAM-001에서 발생한 이벤트를 보여주세요",
        "오늘 발생한 모든 이벤트는?",
        "안전모 미착용 이벤트가 몇 건이나 있나요?",
        "미해결 이벤트 중 심각도가 HIGH인 것들을 찾아주세요",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n[테스트 {i}]")
        print(f"질문: {query}")
        print("-"*60)

        response = agent.query(query)
        print(f"응답: {response}")
        print("="*60)

    print("\n✅ Query Agent 테스트 완료")


if __name__ == "__main__":
    main()