"""
agents/supervisor_langgraph.py
LangGraph 기반 Supervisor — M2 업그레이드

M1 대비 M2 변경사항:
- [M2-1] SqliteSaver Checkpointer → 재시작 후에도 대화 이력 영속
- [M2-2] 메시지 윈도우 → router_node에서 최근 10개 메시지만 유지
- [M2-3] 에러 재시도 루프 → skill_executor 실패 시 router로 재라우팅 (최대 3회)
- [M2-4] 병렬 스킬 실행 → multi_step에서 Send API로 독립 스킬 동시 실행
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Send
from langchain_core.messages import HumanMessage, AIMessage, trim_messages

from agents.state import AgentState
from agents.security_agent import SecurityAgent
from skills.skill_manager import SkillManager
from utils.response_formatter import get_formatter
from config import settings

import json
import re
import os
from typing import Optional, Literal, List

from langchain_google_genai import ChatGoogleGenerativeAI


# ────────────────────────────────────────────────────────────
# 상수
# ────────────────────────────────────────────────────────────
MAX_RETRY = 3          # 스킬 실행 최대 재시도 횟수
MESSAGE_WINDOW = 10    # 대화 이력 유지 메시지 수
DB_PATH = "./data/agent_memory.db"


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
# 노드 1: security_node (M1과 동일)
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
    return {}


def check_security_passed(state: AgentState) -> Literal["pass", "block"]:
    if state.get("error"):
        return "block"
    return "pass"


# ────────────────────────────────────────────────────────────
# 라우팅 테이블 (M1과 동일)
# ────────────────────────────────────────────────────────────
_KEYWORD_MAP = {
    "data_analytics": ["통계", "분석", "추세", "위험도", "비교", "계산", "증감", "변화", "평가"],
    "report_generation": ["보고서", "조치", "방안", "대응", "작성", "생성", "요약", "정리"],
    "knowledge_management": ["검색", "찾아", "알려", "법규", "규정", "어떻게", "무엇", "설명", "안내", "교육"],
    "vision_analysis": ["이미지", "사진", "영상", "PPE", "착용", "감지", "확인"],
}

_DEFAULT_TASK_MAP = {
    "data_analytics": "analyze_query",
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


def _is_safety_domain(user_input: str) -> bool:
    """
    안전 도메인과 최소한의 연관성이 있는지 1차 필터.
    False이면 _llm_route 호출 전 out_of_scope로 빠르게 처리.
    """
    domain_keywords = [
        # 안전 이벤트
        "안전", "사고", "위험", "이벤트", "발생", "낙상", "화재", "연기",
        "PPE", "헬멧", "안전모", "안전조끼", "보호", "접근",
        # 통계/분석
        "통계", "분석", "추세", "비교", "증가", "감소", "현황",
        # 법규/규정
        "법규", "규정", "조항", "산업안전", "기준", "처벌", "벌금",
        # 운영/시스템
        "카메라", "CAM", "CCTV", "모니터링", "보고서", "조치", "대응",
        # 범용 질문 (안전 맥락에서 허용)
        "어떻게", "무엇", "언제", "알려", "설명", "도움",
    ]
    return any(kw in user_input for kw in domain_keywords)


def _quick_route(user_input: str) -> Optional[str]:
    for skill, keywords in _KEYWORD_MAP.items():
        if any(kw in user_input for kw in keywords):
            return skill
    return None


def _llm_route(user_input: str) -> dict:
    prompt = f"""당신은 작업장 안전 모니터링 시스템의 작업 분배 관리자입니다.
오직 작업장 안전, 산업안전, 사고 분석, 법규/규정에 관한 질문만 처리합니다.

사용자 요청: {user_input}

사용 가능한 Skills:
1. data_analytics       - 통계/추세/위험도 분석
2. report_generation    - 보고서/조치방안 작성
3. knowledge_management - 안전 규정 검색 및 Q&A
4. vision_analysis      - 이미지 안전 위반 감지
5. out_of_scope         - 안전 도메인과 무관한 요청 (날씨, 일상, 엔터테인먼트 등)

규칙:
- 안전/사고/법규/모니터링과 관련 없으면 반드시 out_of_scope를 선택하세요.
- 억지로 안전 스킬에 매핑하지 마세요.

응답 형식 (JSON만, 마크다운 없이):
단일: {{"skill": "data_analytics", "task": "구체적 작업", "multi_step": false, "reason": "이유"}}
아웃: {{"skill": "out_of_scope", "task": "", "multi_step": false, "reason": "도메인 외 요청"}}"""  # noqa

    try:
        response = _get_llm().invoke(prompt)
        text = response.content.replace("```json", "").replace("```", "").strip()
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
    except Exception as e:
        print(f"[router_node] LLM 라우팅 오류: {e}")

    return {"skill": "knowledge_management", "task": user_input, "multi_step": False, "reason": "파싱 실패, 기본값"}


def _determine_task(user_input: str, skill_name: str) -> str:
    km = _TASK_KEYWORD_MAP.get(skill_name, {})
    for kw, task_name in km.items():
        if kw in user_input:
            return task_name
    return _DEFAULT_TASK_MAP.get(skill_name, "execute")


# ────────────────────────────────────────────────────────────
# 노드 2: router_node
# [M2-2] 메시지 윈도우: 최근 MESSAGE_WINDOW개 메시지만 유지
# [M2-3] 재시도 시 error/iteration_count 초기화하지 않음 (누적 관리)
# ────────────────────────────────────────────────────────────
def router_node(state: AgentState) -> dict:
    print("\n[router_node] 라우팅 시작")
    user_input = state["user_query"]

    # ── [M2-2] 메시지 윈도우: 최근 N개 메시지만 유지 ──────────
    current_messages = state.get("messages", [])
    if len(current_messages) > MESSAGE_WINDOW:
        trimmed = trim_messages(
            current_messages,
            strategy="last",
            max_tokens=MESSAGE_WINDOW,
            token_counter=len,         # 메시지 개수 기준 카운팅
            allow_partial=False,
        )
        messages_update = trimmed
        print(f"[router_node] 메시지 윈도우: {len(current_messages)} → {len(trimmed)}개")
    else:
        messages_update = current_messages
    # ──────────────────────────────────────────────────────────

    # ── 도메인 관련성 1차 필터 ─────────────────────────────────
    if not _is_safety_domain(user_input):
        print(f"[router_node] 도메인 외 질문 감지 (1차 필터) → out_of_scope")
        oos_answer = (
            "죄송합니다. 저는 작업장 안전 모니터링 전용 시스템입니다.\n"
            "안전 이벤트 분석, 법규 안내, 보고서 작성, 이미지 분석 등\n"
            "안전 관련 질문에만 답변드릴 수 있습니다."
        )
        return {
            "routing_plan": {"skill": "out_of_scope", "multi_step": False},
            "final_answer": oos_answer,
            "messages": messages_update + [AIMessage(content=oos_answer)],
            "error": None,
        }
    # ──────────────────────────────────────────────────────────

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
        print(f"[router_node] LLM 결과: {json.dumps(plan, ensure_ascii=False)}")

        # LLM이 out_of_scope로 판단한 경우
        if plan.get("skill") == "out_of_scope":
            print("[router_node] LLM → out_of_scope")
            oos_answer = (
                "죄송합니다. 저는 작업장 안전 모니터링 전용 시스템입니다.\n"
                "안전 이벤트 분석, 법규 안내, 보고서 작성, 이미지 분석 등\n"
                "안전 관련 질문에만 답변드릴 수 있습니다."
            )
            return {
                "routing_plan": plan,
                "final_answer": oos_answer,
                "messages": messages_update + [AIMessage(content=oos_answer)],
                "error": None,
            }

    return {
        "routing_plan": plan,
        "messages": messages_update,   # 윈도우 적용된 메시지로 교체
        "error": None,                 # 재시도 시 이전 error 초기화
    }


def check_routing(state: AgentState) -> Literal["multi_step", "single", "out_of_scope"]:
    plan = state.get("routing_plan", {})
    if plan.get("skill") == "out_of_scope":
        return "out_of_scope"
    if plan.get("multi_step"):
        return "multi_step"
    return "single"


# ────────────────────────────────────────────────────────────
# 노드 3: skill_executor_node
# [M2-3] 실패 시 iteration_count 증가 (조건부 엣지가 retry/fail 분기)
# ────────────────────────────────────────────────────────────
def skill_executor_node(state: AgentState) -> dict:
    plan = state["routing_plan"]
    skill_name = plan.get("skill", "knowledge_management")
    user_input = state["user_query"]
    task = _determine_task(user_input, skill_name)

    print(f"\n[skill_executor_node] {skill_name} → task: {task} "
          f"(시도 {state.get('iteration_count', 0) + 1}/{MAX_RETRY})")

    context = {
        "query": user_input,
        "task_description": plan.get("task", user_input),
        "previous_results": state.get("skill_results", {}),
    }

    if state.get("image_data"):
        context["images"] = state["image_data"].get("images", [])

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
            # 성공 시 iteration_count는 유지 (이미 시도한 횟수 보존)
        }
    except Exception as e:
        print(f"[skill_executor_node] ❌ 오류: {e}")
        return {
            "error": str(e),
            "current_skill": skill_name,
            "iteration_count": state.get("iteration_count", 0) + 1,
        }


def check_after_skill(state: AgentState) -> Literal["retry", "synthesize", "fail"]:
    """
    [M2-3] skill_executor 이후 분기:
    - error 없음 → synthesize (정상 종료)
    - error 있고 재시도 횟수 미달 → retry (router로 재라우팅)
    - error 있고 재시도 횟수 초과 → fail (에러 응답 생성)
    """
    if not state.get("error"):
        return "synthesize"
    if state.get("iteration_count", 0) < MAX_RETRY:
        print(f"[check_after_skill] 재시도 {state['iteration_count']}/{MAX_RETRY}")
        return "retry"
    print(f"[check_after_skill] 최대 재시도 초과 → fail")
    return "fail"


# ────────────────────────────────────────────────────────────
# 노드 3b: parallel_skill_node  (병렬 실행용 단일 워커)
# [M2-4] Send API가 이 노드를 스킬 수만큼 병렬 호출
# ────────────────────────────────────────────────────────────
def parallel_skill_node(state: AgentState) -> dict:
    """
    Send API로 개별 호출되는 병렬 스킬 실행 노드.
    state에 _current_step 필드(라우터가 Send로 주입)가 있어야 한다.
    """
    step = state.get("_current_step", {})
    skill_name = step.get("skill", "knowledge_management")
    user_input = state["user_query"]
    task = _determine_task(user_input, skill_name)

    print(f"\n[parallel_skill_node] 병렬 실행: {skill_name} → {task}")

    context = {
        "query": user_input,
        "task_description": step.get("task", user_input),
        "previous_results": state.get("skill_results", {}),
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
        if context["previous_results"]:
            context["knowledge_context"] = json.dumps(
                context["previous_results"], ensure_ascii=False
            )[:500]

    try:
        result = _get_skill_manager().execute_skill(skill_name, task, context)
        print(f"[parallel_skill_node] ✅ {skill_name} 완료")
        return {
            "skill_results": {skill_name: result},
            "current_skill": skill_name,
            "error": None,
        }
    except Exception as e:
        print(f"[parallel_skill_node] ❌ {skill_name} 오류: {e}")
        return {
            "skill_results": {skill_name: {"error": str(e), "success": False}},
            "current_skill": skill_name,
        }


# ────────────────────────────────────────────────────────────
# [M2-4] Send API 라우터: 멀티스텝을 병렬로 분기
# ────────────────────────────────────────────────────────────
def route_parallel_skills(state: AgentState) -> List[Send]:
    """
    routing_plan.steps의 각 스텝에 대해 Send를 발행.
    LangGraph는 이 함수가 반환한 Send 목록을 병렬로 실행한다.
    """
    steps = state["routing_plan"].get("steps", [])
    print(f"\n[route_parallel_skills] {len(steps)}개 스킬 병렬 실행")
    return [
        Send("parallel_skill", {**state, "_current_step": step})
        for step in steps
    ]


def parallel_dispatcher_node(state: AgentState) -> dict:
    """
    [M2-4] 멀티스텝 라우팅 시 route_parallel_skills로 Send를 분기하기 전
    경유하는 identity 노드. 상태 변경 없이 그대로 통과.
    """
    steps = state["routing_plan"].get("steps", [])
    print(f"\n[parallel_dispatcher] {len(steps)}개 스킬로 병렬 분기 준비")
    return {}  # 상태 변경 없음


# ────────────────────────────────────────────────────────────
# 노드 5: synthesizer_node (M1과 동일, fail 경로 추가)
# ────────────────────────────────────────────────────────────
def synthesizer_node(state: AgentState) -> dict:
    print("\n[synthesizer_node] 응답 생성")

    plan = state.get("routing_plan", {})
    if plan.get("skill") == "out_of_scope":
        return {}  # router_node에서 이미 final_answer와 messages를 채웠으므로 그대로 통과

    skill_results = state.get("skill_results", {})
    current_skill = state.get("current_skill", "")
    user_query = state["user_query"]

    if not skill_results:
        return {"final_answer": "결과를 생성할 수 없습니다. 다시 시도해주세요."}

    last_raw = skill_results.get(current_skill, {})
    inner_result = last_raw.get("result", last_raw)

    if not last_raw.get("success", True):
        error_msg = last_raw.get("error", "알 수 없는 오류")
        return {"final_answer": f"요청 처리 중 오류가 발생했습니다: {error_msg}"}

    formatter = get_formatter()
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


def error_node(state: AgentState) -> dict:
    """[M2-3] 최대 재시도 초과 시 사용자 친화적 오류 응답"""
    error = state.get("error", "알 수 없는 오류")
    skill = state.get("current_skill", "")
    count = state.get("iteration_count", MAX_RETRY)
    print(f"\n[error_node] {count}회 실패 → 오류 응답 반환")
    return {
        "final_answer": (
            f"요청을 처리하는 과정에서 문제가 발생했습니다.\n"
            f"({skill} 스킬 {count}회 시도 실패)\n"
            f"잠시 후 다시 시도하거나 질문 방식을 바꿔 주세요."
        ),
        "messages": [AIMessage(content=f"[오류] {error}")],
    }


# ────────────────────────────────────────────────────────────
# 헬퍼
# ────────────────────────────────────────────────────────────
def _extract_event_type(user_input: str) -> str:
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
# 그래프 조립 — M2 버전
# ────────────────────────────────────────────────────────────
def build_graph(use_memory: bool = True, use_sqlite: bool = True):
    """
    M2 LangGraph StateGraph 조립 및 컴파일

    Args:
        use_memory:  True이면 Checkpointer로 세션별 대화 이력 유지
        use_sqlite:  True이면 SqliteSaver(영속), False이면 MemorySaver(인메모리)

    Returns:
        Compiled graph

    그래프 구조:
        security → router
                 → skill_executor ──(성공)──→ synthesizer → END
                                  ──(재시도)→ router
                                  ──(실패)──→ error_node → END
                 → [parallel_skill × N] → synthesizer → END
    """
    workflow = StateGraph(AgentState)

    # 노드 등록
    workflow.add_node("security", security_node)
    workflow.add_node("router", router_node)
    workflow.add_node("skill_executor", skill_executor_node)
    workflow.add_node("parallel_dispatcher", parallel_dispatcher_node)  # [M2-4]
    workflow.add_node("parallel_skill", parallel_skill_node)            # [M2-4]
    workflow.add_node("synthesizer", synthesizer_node)
    workflow.add_node("error", error_node)                              # [M2-3]

    # 진입점
    workflow.set_entry_point("security")

    # security → pass/block
    workflow.add_conditional_edges(
        "security",
        check_security_passed,
        {"pass": "router", "block": END},
    )

    # router → single / multi_step / out_of_scope
    workflow.add_conditional_edges(
        "router",
        check_routing,
        {
            "single": "skill_executor",
            "multi_step": "parallel_dispatcher",   # [M2-4] 병렬 분기 노드로
            "out_of_scope": "synthesizer",         # final_answer 이미 설정 → 바로 합성
        },
    )

    # [M2-3] skill_executor → synthesize / retry(router) / fail(error)
    workflow.add_conditional_edges(
        "skill_executor",
        check_after_skill,
        {
            "synthesize": "synthesizer",
            "retry": "router",                     # ← 재라우팅
            "fail": "error",
        },
    )

    # [M2-4] parallel_dispatcher → Send API → parallel_skill × N → synthesizer
    workflow.add_conditional_edges(
        "parallel_dispatcher",
        route_parallel_skills,   # List[Send] 반환
    )
    workflow.add_edge("parallel_skill", "synthesizer")

    # 종료
    workflow.add_edge("synthesizer", END)
    workflow.add_edge("error", END)

    # Checkpointer 설정
    if use_memory:
        if use_sqlite:
            import sqlite3
            os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
            # LangGraph 1.x: from_conn_string()은 context manager 반환 → 직접 연결
            conn = sqlite3.connect(DB_PATH, check_same_thread=False)
            checkpointer = SqliteSaver(conn)
            print(f"[build_graph] SqliteSaver: {DB_PATH}")
        else:
            checkpointer = MemorySaver()
            print("[build_graph] MemorySaver (인메모리)")
        return workflow.compile(checkpointer=checkpointer)

    return workflow.compile()


# ────────────────────────────────────────────────────────────
# SupervisorLangGraph 래퍼 클래스
# ────────────────────────────────────────────────────────────
class SupervisorLangGraph:
    """
    M2 LangGraph 기반 Supervisor.

    주요 M2 기능:
    - SqliteSaver: 재시작 후에도 대화 이력 유지 (thread_id 기준)
    - 메시지 윈도우: 최근 10개 메시지만 라우터에 전달
    - 에러 재시도: 스킬 실패 시 최대 3회 재라우팅
    - 병렬 실행: 멀티스텝 요청 시 Send API로 동시 실행
    """

    def __init__(self, use_memory: bool = True, use_sqlite: bool = True):
        print("✅ SupervisorLangGraph (M2) 초기화 중...")
        self.graph = build_graph(use_memory=use_memory, use_sqlite=use_sqlite)
        self.use_memory = use_memory
        print("✅ SupervisorLangGraph (M2) 초기화 완료")

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
            session_id:  thread_id (Checkpointer 키). SessionManager.get_thread_id()로 생성 권장.

        Returns:
            최종 응답 문자열
        """
        print(f"\n{'='*60}")
        print(f"[SupervisorLangGraph] 요청: {user_input}")
        if session_id:
            print(f"[SupervisorLangGraph] session_id: {session_id}")
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
    # 메모리만 사용 (SQLite 없이 테스트)
    supervisor = SupervisorLangGraph(use_memory=True, use_sqlite=False)

    SESSION = "test_user_001"

    # 멀티턴 대화 테스트 (메시지 이력 누적 확인)
    turns = [
        "안전모를 착용하지 않으면 어떻게 되나요?",
        "방금 말한 내용을 요약해줘",              # 이전 대화 참조 여부 확인
        "최근 7일간 이벤트 통계를 보여주세요",
    ]

    for i, query in enumerate(turns, 1):
        print(f"\n\n{'#'*60}")
        print(f"Turn {i}: {query}")
        print(f"{'#'*60}")
        response = supervisor.execute(query, session_id=SESSION)
        print(f"\n[응답]\n{response}")

    print("\n✅ M2 SupervisorLangGraph 테스트 완료")
