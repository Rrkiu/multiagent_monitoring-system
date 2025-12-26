"""
Report Agent
보고서 생성 및 대응 방안 작성을 전담하는 에이전트
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate

from config import settings
from tools.rag_tools import (
    search_knowledge_base,
    get_action_guide,
    search_safety_regulations
)
from tools.data_tools import get_events_by_date
from tools.analytics_tools import calculate_statistics


class ReportAgent:
    """보고서 생성 전담 에이전트"""

    def __init__(self):
        """Report Agent 초기화"""

        # LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0.3,  # 보고서는 더 일관성 있게
            google_api_key=settings.google_api_key
        )

        # 이 에이전트가 사용할 도구들
        self.tools = [
            search_knowledge_base,
            get_action_guide,
            search_safety_regulations,
            get_events_by_date,
            calculate_statistics,
        ]

        # ReAct 프롬프트 템플릿
        template = """당신은 안전 모니터링 시스템의 보고서 작성 전문가입니다.

                    역할:
                    - 이벤트 데이터를 바탕으로 상세한 보고서를 작성합니다
                    - 각 이벤트에 대한 적절한 조치 방안을 제시합니다
                    - 관련 안전 규정 및 가이드라인을 참조합니다
                    - 전문적이고 명확한 문서를 생성합니다
                    
                    지침:
                    1. 보고서는 구조화되고 읽기 쉬워야 합니다
                    2. 각 이벤트에 대해 구체적인 조치 방안을 제시하세요
                    3. 지식 베이스에서 관련 정보를 찾아 활용하세요
                    4. 우선순위가 높은 항목을 강조하세요
                    5. 실행 가능한 권장 사항을 포함하세요
                    
                    보고서 구성:
                    - 요약 (Summary)
                    - 주요 이벤트 (Key Events)
                    - 통계 (Statistics)
                    - 조치 사항 (Action Items)
                    - 권장 사항 (Recommendations)
                    
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
            max_iterations=7  # 보고서는 더 많은 단계 필요
        )

    def generate_report(self, user_input: str) -> str:
        """
        보고서 생성

        Args:
            user_input: 사용자 입력 (보고서 요청)

        Returns:
            생성된 보고서
        """
        try:
            result = self.agent_executor.invoke({"input": user_input})
            return result.get("output", "보고서를 생성할 수 없습니다.")
        except StopIteration:
            return "보고서 생성 중 오류가 발생했습니다. 요청을 다시 입력해주세요."
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"보고서 생성 중 오류가 발생했습니다: {str(e)}"
def main():
    """테스트용 메인 함수"""
    print("="*60)
    print("Report Agent 테스트")
    print("="*60)

    agent = ReportAgent()

    test_queries = [
        "안전모 미착용 이벤트에 대한 조치 방안을 작성해주세요",
        "작업자 넘어짐 사고에 대한 상세 대응 가이드를 제공해주세요",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n[테스트 {i}]")
        print(f"요청: {query}")
        print("-"*60)

        response = agent.generate_report(query)
        print(f"보고서:\n{response}")
        print("="*60)

    print("\n✅ Report Agent 테스트 완료")


if __name__ == "__main__":
    main()