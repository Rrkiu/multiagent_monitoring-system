"""
agents/supervisor_langgraph.py
LangGraph 기반 Supervisor — StateGraph로 전체 흐름 관리

기존 supervisor_v2.py (LangChain) 대비 변경점:
- AgentState로 구조화된 상태 공유
- SecurityAgent → security_node (그래프 첫 번째 노드)
- quick_route/llm_route → router_node
- _execute_skill → skill_executor_node
- ResponseFormatter → synthesizer_node
- 조건부 엣지로 보안 차단 / 멀티스텝 분기 처리
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import HumanMessage, AIMessage

from agents.state import AgentState
from agents.security_agent import SecurityAgent
from skills.skill_manager import SkillManager
from utils.response_formatter import get_formatter
from config import settings

import json
import re
from typing import Optional, Literal

from langchain_google_genai import ChatGoogleGenerativeAI


# ────────────────────────────────────────────────────────────
# 공유 싱글톤
# ────────────────────────────────────────────────────────────
_security_agent: Optional[SecurityAgent] = None
_skill_manager: Optional[SkillManager] = None
_llm = None


def _get_security_agent() -> SecurityAgent:
    global _security_agent
    if _security_agent is None:
        _security_agent = SecurityAgent()
    return _security_agent


def _get_skill_manager() -> SkillManager:
    global _skill_manager
    if _skill_manager is None:
        _skill_manager = SkillManager()
    return _skill_manager


def _get_llm():
    global _llm
    if _llm is None:
        _llm = ChatGoogleGenerativeAI(
            model=settings.llm_model,
            temperature=0.0,
            google_api_key=settings.google_api_key,
        )
    return _llm


# ────────────────────────────────────────────────────────────
# 노드 1: security_node
#   - 기존 app.py 레벨 SecurityAgent 검사를 그래프 안으로 편입
#   - 차단되면 final_answer에 메시지를 담고 error를 설정
#   - 이후 check_security_passed() 조건 함수가 END로 직행시킴
# ────────────────────────────────────────────────────────────
def security_node(state: AgentState) -> dict:
    print("\n[security_node] 보안 검사 시작")
    security = _get_security_agent()
    is_safe, reason = security.check_safety(state["user_query"])

    if not is_safe:
        print(f"[security_node] ❌ 차단: {reason}")
        return {
            "final_answer": f"보안 정책상 해당 요청은 처리할 수 없습니다. 사유: {reason}",
            "error": reason,
            "messages": [AIMessage(content=f"[보안 차단] {reason}")],
        }

    print("[security_node] ✅ 통과")
    return {}  # 변경 없음 — 다음 노드로 그대로 전달


def check_security_passed(state: AgentState) -> Literal["pass", "block"]:
    """security_node 이후 조건 함수: 오류 있으면 즉시 종료"""
    if state.get("error"):
        return "block"
    return "pass"


# ────────────────────────────────────────────────────────────
# 노드 2: router_node
#   - 기존 quick_route() + llm_route() 로직을 그대로 이식
#   - State에 routing_plan 저장
# ────────────────────────────────────────────────────────────

# 키워드 기반 빠른 라우팅 매핑 (LLM 호출 없음)
_KEYWORD_MAP = {
    "data_analytics": ["통계", "분석", "추세", "위험도", "비교", "계산", "증감", "변화", "평가"],
    "report_generation": ["보고서", "조치", "방안", "대응", "작성", "생성", "요약", "정리"],
    "knowledge_management": ["검색", "찾아", "알려", "법규", "규정", "어떻게", "무엇", "설명", "안내", "교육"],
    "vision_analysis": ["이미지", "사진", "영상", "PPE", "착용", "감지", "확인"],
}

_DEFAULT_TASK_MAP = {
    "data_analytics": "analyze_query",   # 자연어 쿼리 → LLM이 파라미터 추출
    "report_generation": "generate_action_plan",
    "knowledge_management": "search_knowledge",
    "vision_analysis": "analyze_image",
}

_TASK_KEYWORD_MAP = {
    "data_analytics": {
        "추세": "analyze_trend",
        "위험도": "assess_risk",
        "많은": "find_top_cameras",
        "위험한": "assess_risk",
        # 그 외 자연어 통계 요청은 analyze_query로 처리 (LLM이 날짜 추출)
    },
    "report_generation": {
        "조치": "generate_action_plan", "대응": "generate_action_plan", "방안": "generate_action_plan",
        "일일": "generate_daily_report", "주간": "generate_weekly_report",
        "사고": "generate_incident_report", "보고서": "generate_event_report",
    },
    "knowledge_management": {
        "법규": "search_regulations", "규정": "search_regulations",
        "찾아": "search_knowledge", "알려": "answer_question",
    },
    "vision_analysis": {"PPE": "detect_ppe", "착용": "detect_ppe", "비교": "compare_images"},
}


def _quick_route(user_input: str) -> Optional[str]:
    """키워드 매칭으로 즉시 스킬 결정 (LLM 호출 없음)"""
    for skill, keywords in _KEYWORD_MAP.items():
        if any(kw in user_input for kw in keywords):
            return skill
    return None


def _llm_route(user_input: str) -> dict:
    """LLM을 호출하여 라우팅 계획을 JSON으로 결정"""
    prompt = f"""당신은 안전 모니터링 시스템의 작업 분배 관리자입니다.

사용자 요청: {user_input}

사용 가능한 Skills:
1. data_analytics     - 통계/추세/위험도 분석
2. report_generation  - 보고서/조치방안 작성
3. knowledge_management - 안전 규정 검색 및 Q&A (RAG)
4. vision_analysis    - 이미지 안전 위반 감지

복잡한 요청은 여러 Skills를 순차 사용:
- 예: "위험 구역 대응 방안" → data_analytics → report_generation

응답 형식 (JSON만):
단일: {{"skill": "data_analytics", "task": "구체적 작업", "multi_step": false, "reason": "이유"}}
멀티: {{"multi_step": true, "steps": [{{"skill": "data_analytics", "task": "작업1"}}, {{"skill": "report_generation", "task": "작업2"}}], "reason": "이유"}}"""

    try:
        response = _get_llm().invoke(prompt)
        text = response.content.replace("```json", "").replace("```", "").strip()
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"[router_node] LLM 라우팅 오류: {e}")

    # 기본값
    return {"skill": "knowledge_management", "task": user_input, "multi_step": False, "reason": "파싱 실패, 기본값"}


def _determine_task(user_input: str, skill_name: str) -> str:
    """스킬별 세부 task 이름 결정"""
    km = _TASK_KEYWORD_MAP.get(skill_name, {})
    for kw, task_name in km.items():
        if kw in user_input:
            return task_name
    return _DEFAULT_TASK_MAP.get(skill_name, "execute")


def router_node(state: AgentState) -> dict:
    print("\n[router_node] 라우팅 시작")
    user_input = state["user_query"]

    # 1단계: 빠른 키워드 라우팅
    skill_name = _quick_route(user_input)
    if skill_name:
        print(f"[router_node] 빠른 라우팅 → {skill_name}")
        plan = {
            "skill": skill_name,
            "task": user_input,
            "multi_step": False,
            "reason": "키워드 매칭",
        }
    else:
        # 2단계: LLM 라우팅
        print("[router_node] LLM 라우팅 시작")
        plan = _llm_route(user_input)
        print(f"[router_node] LLM 라우팅 결과: {json.dumps(plan, ensure_ascii=False)}")

    return {
        "routing_plan": plan,
        "iteration_count": 0,
        "error": None,
        "messages": [HumanMessage(content=user_input)],
    }


def check_routing(state: AgentState) -> Literal["multi_step", "single"]:
    """router_node 이후 조건 함수: 멀티스텝 여부로 분기"""
    if state["routing_plan"].get("multi_step"):
        return "multi_step"
    return "single"


# ────────────────────────────────────────────────────────────
# 노드 3: skill_executor_node  (단일 스텝용)
#   - routing_plan의 skill/task를 SkillManager로 실행
#   - raw dict 결과를 skill_results에 누적 저장
# ────────────────────────────────────────────────────────────
def skill_executor_node(state: AgentState) -> dict:
    plan = state["routing_plan"]
    skill_name = plan.get("skill", "knowledge_management")
    user_input = state["user_query"]

    # task 이름 결정 (LLM 라우팅이 task를 줬으면 그것 우선, 없으면 키워드 매핑)
    task = _determine_task(user_input, skill_name)

    print(f"\n[skill_executor_node] {skill_name} → task: {task}")

    # context 구성 — 이전 스텝 결과를 구조화된 형태로 전달
    context = {
        "query": user_input,
        "task_description": plan.get("task", user_input),
        "previous_results": state.get("skill_results", {}),
    }

    # 이미지 데이터 추가 (vision_analysis용)
    if state.get("image_data"):
        context["images"] = state["image_data"].get("images", [])

    # report_generation 필수 context 보완
    if skill_name == "report_generation":
        if task == "generate_action_plan":
            context["event_data"] = {
                "event_type": _extract_event_type(user_input),
                "description": user_input,
                "severity": "MEDIUM",
                "timestamp": "N/A",
            }
            context["knowledge_context"] = f"사용자 질문: {user_input}"
        elif task in ("generate_event_report", "generate_statistics_report"):
            context.setdefault("events", [])
            context.setdefault("statistics", {})

    try:
        result = _get_skill_manager().execute_skill(
            skill_name=skill_name,
            task=task,
            context=context,
        )
        print(f"[skill_executor_node] ✅ 성공")
        return {
            "skill_results": {skill_name: result},
            "current_skill": skill_name,
            "error": None,
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"[skill_executor_node] ❌ 오류: {e}")
        return {
            "error": str(e),
            "current_skill": skill_name,
            "iteration_count": state.get("iteration_count", 0) + 1,
        }


# ────────────────────────────────────────────────────────────
# 노드 3b: multi_step_executor_node  (멀티스텝용)
#   - routing_plan.steps를 순서대로 실행
#   - 각 스텝 raw 결과를 skill_results에 누적
#   - 이전 스텝 결과를 context["previous_results"]로 구조화 전달
# ────────────────────────────────────────────────────────────
def multi_step_executor_node(state: AgentState) -> dict:
    plan = state["routing_plan"]
    steps = plan.get("steps", [])
    user_input = state["user_query"]

    print(f"\n[multi_step_executor_node] {len(steps)}개 스텝 실행")

    accumulated_results: dict = {}

    for i, step in enumerate(steps, 1):
        skill_name = step.get("skill", "knowledge_management")
        task = _determine_task(user_input, skill_name)

        print(f"  [Step {i}/{len(steps)}] {skill_name} → {task}")

        context = {
            "query": user_input,
            "task_description": step.get("task", user_input),
            # 이전 스텝의 raw dict 결과를 그대로 전달 (문자열 concat 아님)
            "previous_results": accumulated_results,
        }

        if state.get("image_data"):
            context["images"] = state["image_data"].get("images", [])

        if skill_name == "report_generation" and task == "generate_action_plan":
            context["event_data"] = {
                "event_type": _extract_event_type(user_input),
                "description": user_input,
                "severity": "MEDIUM",
                "timestamp": "N/A",
            }
            # 이전 스텝 결과가 있으면 knowledge_context로 활용
            if accumulated_results:
                prev_summary = json.dumps(accumulated_results, ensure_ascii=False)[:500]
                context["knowledge_context"] = prev_summary

        try:
            result = _get_skill_manager().execute_skill(
                skill_name=skill_name,
                task=task,
                context=context,
            )
            accumulated_results[skill_name] = result
            print(f"  [Step {i}] ✅ 완료")
        except Exception as e:
            print(f"  [Step {i}] ❌ 오류: {e}")
            accumulated_results[skill_name] = {"error": str(e)}

    # 마지막으로 실행된 스킬 이름
    last_skill = steps[-1].get("skill") if steps else "knowledge_management"

    return {
        "skill_results": accumulated_results,
        "current_skill": last_skill,
        "error": None,
    }


# ────────────────────────────────────────────────────────────
# 노드 4: synthesizer_node
#   - skill_results의 마지막 결과를 ResponseFormatter로 자연어 변환
#   - final_answer에 저장
# ────────────────────────────────────────────────────────────
def synthesizer_node(state: AgentState) -> dict:
    print("\n[synthesizer_node] 응답 생성")

    skill_results = state.get("skill_results", {})
    current_skill = state.get("current_skill", "")
    user_query = state["user_query"]

    if not skill_results:
        return {"final_answer": "결과를 생성할 수 없습니다. 다시 시도해주세요."}

    # 마지막 스킬의 raw 결과 추출
    # SkillManager.execute_skill() 반환: {"success": bool, "skill": ..., "task": ..., "result": {...}}
    last_raw = skill_results.get(current_skill, {})
    inner_result = last_raw.get("result", last_raw)  # result 키가 있으면 그 안, 없으면 전체

    # 실패한 경우
    if not last_raw.get("success", True):
        error_msg = last_raw.get("error", "알 수 없는 오류")
        return {"final_answer": f"요청 처리 중 오류가 발생했습니다: {error_msg}"}

    formatter = get_formatter()
    # routing_plan에서 task 이름 확인
    plan = state.get("routing_plan", {})
    task_name = _determine_task(user_query, current_skill)

    formatted = formatter.format_response(
        raw_result=inner_result,
        user_query=user_query,
        skill_name=current_skill,
        task=task_name,
    )

    print(f"[synthesizer_node] ✅ 응답 생성 완료 ({len(formatted)}자)")
    return {
        "final_answer": formatted,
        "messages": [AIMessage(content=formatted)],
    }


# ────────────────────────────────────────────────────────────
# 헬퍼
# ────────────────────────────────────────────────────────────
def _extract_event_type(user_input: str) -> str:
    """사용자 입력에서 이벤트 타입 추출"""
    mapping = {
        "NO_HELMET": ["헬멧", "안전모"],
        "NO_SAFETY_VEST": ["조끼", "안전조끼"],
        "FALL_DETECTED": ["낙상", "넘어짐", "추락"],
        "FIRE_HAZARD": ["화재", "불", "연기"],
        "RESTRICTED_AREA": ["제한구역", "출입금지"],
        "EQUIPMENT_MISUSE": ["장비", "기계"],
    }
    for event_type, keywords in mapping.items():
        if any(kw in user_input for kw in keywords):
            return event_type
    return "UNKNOWN"


# ────────────────────────────────────────────────────────────
# 그래프 조립
# ────────────────────────────────────────────────────────────
def build_graph(use_memory: bool = False):
    """
    LangGraph StateGraph 조립 및 컴파일

    Args:
        use_memory: True이면 MemorySaver로 세션별 대화 이력 유지

    Returns:
        Compiled graph
    """
    workflow = StateGraph(AgentState)

    # 노드 등록
    workflow.add_node("security", security_node)
    workflow.add_node("router", router_node)
    workflow.add_node("skill_executor", skill_executor_node)
    workflow.add_node("multi_step_executor", multi_step_executor_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # 진입점
    workflow.set_entry_point("security")

    # 엣지 정의
    # security → (pass) router / (block) END
    workflow.add_conditional_edges(
        "security",
        check_security_passed,
        {"pass": "router", "block": END},
    )

    # router → (single) skill_executor / (multi_step) multi_step_executor
    workflow.add_conditional_edges(
        "router",
        check_routing,
        {"single": "skill_executor", "multi_step": "multi_step_executor"},
    )

    # skill_executor → synthesizer (항상)
    workflow.add_edge("skill_executor", "synthesizer")

    # multi_step_executor → synthesizer (항상)
    workflow.add_edge("multi_step_executor", "synthesizer")

    # synthesizer → END
    workflow.add_edge("synthesizer", END)

    # 컴파일
    if use_memory:
        memory = MemorySaver()
        return workflow.compile(checkpointer=memory)

    return workflow.compile()


# ────────────────────────────────────────────────────────────
# SupervisorLangGraph — app.py에서 기존 SupervisorAgentV2와
# 동일한 인터페이스로 교체할 수 있는 래퍼 클래스
# ────────────────────────────────────────────────────────────
class SupervisorLangGraph:
    """
    LangGraph 기반 Supervisor.
    app.py에서 SupervisorAgentV2 드롭인 교체 가능:

        # 기존
        from agents.supervisor_v2 import SupervisorAgentV2
        supervisor = SupervisorAgentV2()
        response = supervisor.execute(query)

        # 신규
        from agents.supervisor_langgraph import SupervisorLangGraph
        supervisor = SupervisorLangGraph()
        response = supervisor.execute(query)
    """

    def __init__(self, use_memory: bool = True):
        print("✅ SupervisorLangGraph 초기화 중...")
        self.graph = build_graph(use_memory=use_memory)
        self.use_memory = use_memory
        print("✅ SupervisorLangGraph 초기화 완료")

    def execute(
        self,
        user_input: str,
        image_data: Optional[dict] = None,
        session_id: Optional[str] = None,
    ) -> str:
        """
        사용자 요청 실행

        Args:
            user_input:  사용자 질의
            image_data:  {"images": [base64, ...]} (멀티모달)
            session_id:  세션 ID (메모리 사용 시 대화 이력 연결)

        Returns:
            최종 응답 문자열
        """
        print(f"\n{'='*60}")
        print(f"[SupervisorLangGraph] 요청: {user_input}")
        print(f"{'='*60}")

        initial_state: AgentState = {
            "messages": [],
            "user_query": user_input,
            "image_data": image_data,
            "routing_plan": {},
            "current_skill": "",
            "skill_results": {},
            "final_answer": "",
            "error": None,
            "iteration_count": 0,
        }

        config = {}
        if self.use_memory and session_id:
            config = {"configurable": {"thread_id": session_id}}

        try:
            result = self.graph.invoke(initial_state, config)
            answer = result.get("final_answer", "")
            if not answer or not answer.strip():
                return "죄송합니다. 응답을 생성할 수 없습니다. 다시 시도해주세요."
            return answer
        except Exception as e:
            import traceback
            traceback.print_exc()
            return f"요청 처리 중 오류가 발생했습니다: {str(e)}"


# ────────────────────────────────────────────────────────────
# 단독 실행 테스트
# ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    supervisor = SupervisorLangGraph(use_memory=False)

    test_queries = [
        "안전모를 착용하지 않으면 어떻게 되나요?",
        "최근 7일간 통계를 보여주세요",
        "낙상 사고에 대한 조치 방안을 알려주세요",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n\n{'#'*60}")
        print(f"테스트 {i}: {query}")
        print(f"{'#'*60}")
        response = supervisor.execute(query)
        print(f"\n[최종 응답]\n{response}")
        print(f"\n{'='*60}")

    print("\n✅ SupervisorLangGraph 테스트 완료")
