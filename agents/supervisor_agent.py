"""
Supervisor Agent
전체 시스템을 조율하고 적절한 하위 에이전트에게 작업을 위임하는 에이전트
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from config import settings
from agents.query_agent import QueryAgent
from agents.analysis_agent import AnalysisAgent
from agents.report_agent import ReportAgent
from agents.search_agent import SearchAgent
from agents.multimodal_agent import MultimodalAgent
import json
import re


class SupervisorAgent:
    """전체 시스템을 조율하는 Supervisor Agent"""

    def __init__(self):
        """Supervisor Agent 초기화"""

        # LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0.0,
            google_api_key=settings.google_api_key
        )

        # 하위 에이전트들 초기화
        self.query_agent = QueryAgent()
        self.analysis_agent = AnalysisAgent()
        self.report_agent = ReportAgent()
        self.search_agent = SearchAgent()
        self.multimodal_agent = MultimodalAgent()

        # 에이전트 매핑
        self.agents_map = {
            "query": self.query_agent,
            "analysis": self.analysis_agent,
            "report": self.report_agent,
            "search": self.search_agent,
            "multimodal": self.multimodal_agent,
        }

    def route(self, user_input: str) -> dict:
        """
        사용자 입력을 분석하여 어떤 에이전트를 사용할지 결정

        Args:
            user_input: 사용자 입력

        Returns:
            라우팅 계획 (agent, query, multi_step 여부)
        """

        routing_prompt = f"""당신은 안전 모니터링 시스템의 작업 분배 관리자입니다.

                        사용자 요청: {user_input}
                        
                        사용 가능한 에이전트:
                        1. query - 데이터 조회 전담
                           - 특정 카메라의 이벤트 조회
                           - 특정 날짜의 이벤트 조회
                           - 특정 타입의 이벤트 조회
                           - 미해결 이벤트 조회
                           - 카메라 목록 조회
                           예: "CAM-001의 이벤트 보여줘", "오늘 발생한 이벤트는?"
                        
                        2. analysis - 데이터 분석 전담
                           - 통계 계산
                           - 추세 분석
                           - 위험도 평가
                           - 가장 문제가 많은 구역 찾기
                           예: "통계 분석해줘", "가장 위험한 카메라는?", "증감률 계산"
                        
                        3. report - 보고서 및 대응 방안 작성
                           - 일일 보고서 생성
                           - 조치 방안 제공
                           - 안전 규정 안내 (내부 지식 베이스 활용)
                           - 외부 정보 요청 시에도 내부 지식으로 답변
                           예: "보고서 작성해줘", "대응 방안 알려줘", "조치 사항은?"
                           예: "산업안전보건법 내용", "안전 규정 안내"
                        
                        4. multimodal - 이미지 분석 전담 (NEW!)
                           - 이미지에서 안전 위반 사항 감지
                           - PPE(개인 보호 장비) 착용 여부 확인
                           - 작업장 안전 상태 평가
                           - 이미지 기반 질의응답
                           - CCTV 스냅샷 분석
                           예: "이 이미지 분석해줘", "안전모 착용 확인", "작업장 안전 상태는?"
                           주의: 이미지가 제공된 경우에만 사용
                        
                        중요: 외부 웹 검색 기능은 현재 사용 불가능합니다.
                        최신 정보나 외부 규정 관련 질문은 report 에이전트가 내부 지식 베이스를 활용하여 답변합니다.
                        
                        사용자 요청을 분석하여 어떤 에이전트를 사용할지 결정하세요.
                        
                        복잡한 요청의 경우 여러 에이전트를 순차적으로 사용할 수 있습니다:
                        - 예: "가장 위험한 구역의 대응 방안" → analysis (위험 구역 찾기) → report (대응 방안)
                        - 예: "오늘 이벤트 보고서" → query (데이터 조회) → report (보고서 생성)
                        - 예: "이 이미지의 위험 요소와 대응 방안" → multimodal (이미지 분석) → report (대응 방안)
                        
                        응답 형식 (JSON만):
                        {{
                          "agent": "query" | "analysis" | "report" | "multimodal",
                          "reason": "선택 이유",
                          "multi_step": false,
                          "steps": []
                        }}
                        
                        또는 멀티스텝인 경우:
                        {{
                          "multi_step": true,
                          "steps": [
                            {{"agent": "query", "task": "구체적인 작업"}},
                            {{"agent": "report", "task": "구체적인 작업"}}
                          ],
                          "reason": "멀티스텝 이유"
                        }}"""

        try:
            response = self.llm.invoke(routing_prompt)
            response_text = response.content.replace('```json', '').replace('```', '').strip()

            # JSON 추출
            json_match = re.search(r'\{[\s\S]*\}', response_text)

            if not json_match:
                # 기본값: query 에이전트
                return {
                    "agent": "query",
                    "multi_step": False,
                    "reason": "파싱 실패, 기본값 사용"
                }

            routing_plan = json.loads(json_match.group())
            
            # search 에이전트가 선택된 경우 report로 대체
            if routing_plan.get("agent") == "search":
                routing_plan["agent"] = "report"
                routing_plan["reason"] = f"원래 search 선택됨 → report로 대체 (웹 검색 비활성화). {routing_plan.get('reason', '')}"
            
            # 멀티스텝에서 search 제거
            if routing_plan.get("multi_step") and "steps" in routing_plan:
                for step in routing_plan["steps"]:
                    if step.get("agent") == "search":
                        step["agent"] = "report"
                        step["task"] = f"내부 지식 베이스로 답변: {step.get('task', '')}"
            
            return routing_plan

        except Exception as e:
            print(f"라우팅 오류: {e}")
            return {
                "agent": "query",
                "multi_step": False,
                "reason": f"오류 발생: {str(e)}"
            }

    def execute(self, user_input: str) -> str:
        """
        사용자 요청 실행

        Args:
            user_input: 사용자 입력

        Returns:
            최종 응답
        """
        print(f"\n{'=' * 60}")
        print(f"사용자 요청: {user_input}")
        print(f"{'=' * 60}")

        # 1단계: 라우팅
        routing_plan = self.route(user_input)
        print(f"\n[라우팅 계획]")
        print(json.dumps(routing_plan, ensure_ascii=False, indent=2))

        # 2단계: 실행
        try:
            if routing_plan.get("multi_step"):
                # 멀티스텝 실행
                return self._execute_multi_step(routing_plan, user_input)
            else:
                # 단일 에이전트 실행
                agent_name = routing_plan.get("agent", "query")
                return self._execute_single_agent(agent_name, user_input)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"요청 처리 중 오류가 발생했습니다: {str(e)}"

    def _execute_single_agent(self, agent_name: str, user_input: str, image_data: dict = None) -> str:
        """단일 에이전트 실행"""
        print(f"\n[실행] {agent_name} 에이전트")
        print(f"{'=' * 60}")

        try:
            if agent_name == "query":
                return self.query_agent.query(user_input)
            elif agent_name == "analysis":
                return self.analysis_agent.analyze(user_input)
            elif agent_name == "report":
                return self.report_agent.generate_report(user_input)
            elif agent_name == "search":
                return self.search_agent.search(user_input)
            elif agent_name == "multimodal":
                # 이미지 데이터가 있는 경우
                if image_data:
                    images = image_data.get("images", [])
                    if len(images) == 1:
                        return self.multimodal_agent.analyze_image(images[0], user_input)
                    elif len(images) > 1:
                        return self.multimodal_agent.analyze_multiple_images(images, user_input)
                    else:
                        return "이미지가 제공되지 않았습니다."
                else:
                    return "멀티모달 에이전트는 이미지가 필요합니다."
            else:
                return f"알 수 없는 에이전트: {agent_name}"
        except StopIteration:
            return f"{agent_name} 에이전트가 응답을 생성하지 못했습니다. 다시 시도해주세요."
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"{agent_name} 에이전트 실행 중 오류: {str(e)}"

    def _execute_multi_step(self, routing_plan: dict, original_input: str) -> str:
        """멀티스텝 실행"""
        print(f"\n[멀티스텝 실행]")

        steps = routing_plan.get("steps", [])
        results = []
        context = ""

        for i, step in enumerate(steps, 1):
            agent_name = step.get("agent")
            task = step.get("task", original_input)

            print(f"\n[Step {i}/{len(steps)}] {agent_name} - {task}")
            print(f"{'-' * 60}")

            # 이전 단계의 결과를 컨텍스트로 추가
            if context:
                task_with_context = f"{task}\n\n이전 단계 결과:\n{context}"
            else:
                task_with_context = task

            # 에이전트 실행
            result = self._execute_single_agent(agent_name, task_with_context)
            results.append({
                "step": i,
                "agent": agent_name,
                "task": task,
                "result": result
            })

            context = result
            print(f"\n[Step {i} 결과]\n{result[:200]}...")

        # 최종 결과 통합
        final_result = self._synthesize_results(results, original_input)
        return final_result

    def _synthesize_results(self, results: list, original_input: str) -> str:
        """멀티스텝 결과를 통합"""

        # 마지막 단계의 결과를 주로 사용하되, 필요시 이전 결과도 참고
        if not results:
            return "결과가 없습니다."

        if len(results) == 1:
            return results[0]["result"]

        # 여러 단계의 결과를 LLM에게 요약 요청
        synthesis_prompt = f"""다음은 사용자 요청을 처리한 여러 단계의 결과입니다.

                        사용자 원래 요청: {original_input}
                        
                        단계별 결과:
                        """
        for r in results:
            synthesis_prompt += f"\n[{r['step']}단계 - {r['agent']}]\n작업: {r['task']}\n결과: {r['result']}\n"

        synthesis_prompt += """

                            위 모든 단계의 결과를 종합하여 사용자의 원래 요청에 대한 최종 답변을 작성하세요.
                            - 모든 관련 정보를 포함하세요
                            - 명확하고 구조화된 형태로 제시하세요
                            - 한국어로 작성하세요
                            """

        try:
            response = self.llm.invoke(synthesis_prompt)
            return response.content
        except Exception as e:
            # 통합 실패 시 마지막 결과 반환
            return results[-1]["result"]


def main():
    """테스트용 메인 함수"""
    print("=" * 60)
    print("Supervisor Agent 테스트")
    print("=" * 60)

    supervisor = SupervisorAgent()

    test_queries = [
        # 단순 조회
        "CAM-001에서 발생한 이벤트를 보여주세요",

        # 분석
        "2025-11-15부터 2025-11-22까지 가장 이벤트가 많은 카메라는?",

        # 보고서
        "안전모 미착용에 대한 조치 방안을 알려주세요",

        # 멀티스텝
        "최근 7일간 가장 위험한 구역의 대응 방안을 제시해주세요",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n\n{'#' * 60}")
        print(f"테스트 {i}")
        print(f"{'#' * 60}")

        response = supervisor.execute(query)

        print(f"\n{'=' * 60}")
        print(f"[최종 응답]")
        print(f"{'=' * 60}")
        print(response)
        print(f"\n{'=' * 60}\n")

    print("\n✅ Supervisor Agent 테스트 완료")


if __name__ == "__main__":
    main()