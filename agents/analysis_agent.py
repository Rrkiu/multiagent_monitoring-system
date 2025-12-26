"""
Analysis Agent - 간소화 버전
직접 Tool 호출 방식 사용
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import datetime, timedelta
from config import settings
from tools.analytics_tools import (
    calculate_statistics,
    find_top_event_camera,
    calculate_trend,
    assess_risk_level
)
import json
import re


class AnalysisAgent:
    """분석 전담 에이전트 - 간소화 버전"""

    def __init__(self):
        """Analysis Agent 초기화"""

        # LLM 초기화
        self.llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0.0,
            google_api_key=settings.google_api_key
        )

        # 도구 매핑
        self.tools_map = {
            "calculate_statistics": calculate_statistics,
            "find_top_event_camera": find_top_event_camera,
            "calculate_trend": calculate_trend,
            "assess_risk_level": assess_risk_level,
        }

    def _get_current_date_info(self):
        """현재 날짜 정보 반환"""
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        week_ago = today - timedelta(days=7)
        two_weeks_ago = today - timedelta(days=14)
        month_ago = today - timedelta(days=30)

        return f"""
오늘 날짜: {today.strftime('%Y-%m-%d')}
어제 날짜: {yesterday.strftime('%Y-%m-%d')}
7일 전: {week_ago.strftime('%Y-%m-%d')}
14일 전: {two_weeks_ago.strftime('%Y-%m-%d')}
30일 전: {month_ago.strftime('%Y-%m-%d')}

참고: "최근 7일", "이번 주" 등의 표현은 위 날짜를 참고하여 구체적인 날짜로 변환하세요.
"""

    def analyze(self, user_input: str) -> str:
        """사용자 분석 요청 처리"""

        date_info = self._get_current_date_info()

        # 1단계: LLM에게 어떤 도구를 사용할지 물어보기
        planning_prompt = f"""당신은 안전 모니터링 시스템의 데이터 분석 전문가입니다.

                        현재 날짜 정보:
                        {date_info}
                        
                        사용자 요청: {user_input}
                        
                        사용 가능한 도구:
                        1. calculate_statistics
                           - 파라미터: start_date (YYYY-MM-DD 형식), end_date (YYYY-MM-DD 형식)
                           - 예시: {{"start_date": "2025-11-15", "end_date": "2025-11-22"}}
                        
                        2. find_top_event_camera
                           - 파라미터: start_date (YYYY-MM-DD), end_date (YYYY-MM-DD), limit (숫자, 선택사항)
                           - 예시: {{"start_date": "2025-11-15", "end_date": "2025-11-22", "limit": 3}}
                        
                        3. calculate_trend
                           - 파라미터: current_start, current_end, previous_start, previous_end (모두 YYYY-MM-DD)
                           - 예시: {{"current_start": "2025-11-15", "current_end": "2025-11-22", "previous_start": "2025-11-08", "previous_end": "2025-11-14"}}
                        
                        4. assess_risk_level
                           - 파라미터: camera_id (선택사항, 예: "CAM-001"), days (숫자)
                           - 예시: {{"days": 7}} 또는 {{"camera_id": "CAM-001", "days": 7}}
                        
                        중요: 
                        - 날짜는 반드시 YYYY-MM-DD 형식으로 제공하세요
                        - "7일 전", "오늘" 같은 상대적 표현을 사용하지 말고, 위의 날짜 정보를 참고하여 구체적인 날짜를 사용하세요
                        
                        어떤 도구를 사용해야 하는지, 그리고 파라미터는 무엇인지 JSON 형식으로만 답변하세요.
                        
                        응답 형식 (다른 설명 없이 JSON만):
                        {{
                          "tool": "도구_이름",
                          "parameters": {{
                            "param1": "value1",
                            "param2": "value2"
                          }}
                        }}"""

        try:
            # LLM에게 계획 요청
            planning_response = self.llm.invoke(planning_prompt)
            planning_text = planning_response.content

            print(f"\n[계획 응답]\n{planning_text}\n")

            # JSON 추출 (마크다운 코드 블록 제거)
            planning_text = planning_text.replace('```json', '').replace('```', '').strip()
            json_match = re.search(r'\{[\s\S]*\}', planning_text)
            if not json_match:
                return "도구 선택에 실패했습니다. 질문을 더 구체적으로 입력해주세요."

            plan = json.loads(json_match.group())
            tool_name = plan.get("tool")
            parameters = plan.get("parameters", {})

            # 도구 실행
            if tool_name not in self.tools_map:
                return f"알 수 없는 도구: {tool_name}"

            tool = self.tools_map[tool_name]
            print(f"[실행] {tool_name}")
            print(f"[파라미터] {json.dumps(parameters, ensure_ascii=False, indent=2)}")

            result = tool.invoke(parameters)

            print(f"\n[결과 미리보기]\n{result[:200]}...\n")

            # 2단계: 결과를 자연어로 설명
            explanation_prompt = f"""다음은 {tool_name} 도구의 실행 결과입니다:

                                {result}
                                
                                사용자 요청: {user_input}
                                
                                위 데이터를 바탕으로 사용자가 이해하기 쉽도록 한국어로 설명해주세요.
                                - 구체적인 숫자와 퍼센트를 포함하세요
                                - 주요 인사이트를 강조하세요
                                - 필요하면 권장 사항을 제시하세요
                                - 명확하고 간결하게 작성하세요"""

            explanation_response = self.llm.invoke(explanation_prompt)
            return explanation_response.content

        except json.JSONDecodeError as e:
            return f"응답 형식 오류가 발생했습니다. 질문을 다시 입력해주세요."
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"분석 처리 중 오류가 발생했습니다: {str(e)}"


def main():
    """테스트용 메인 함수"""
    print("="*60)
    print("Analysis Agent 테스트 (간소화 버전)")
    print("="*60)

    agent = AnalysisAgent()

    test_queries = [
        "2025-11-15부터 2025-11-22까지의 통계를 분석해주세요",
        "2025-11-15부터 2025-11-22까지 가장 이벤트가 많이 발생한 카메라는 어디인가요?",
        "최근 7일간 전체 시스템의 위험도를 평가해주세요",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n[테스트 {i}]")
        print(f"질문: {query}")
        print("-"*60)

        response = agent.analyze(query)
        print(f"\n응답:\n{response}")
        print("="*60)

    print("\n✅ Analysis Agent 테스트 완료")


if __name__ == "__main__":
    main()