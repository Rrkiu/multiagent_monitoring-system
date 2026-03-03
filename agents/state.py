"""
agents/state.py
LangGraph 전체 그래프에서 공유되는 AgentState 정의
"""

from typing import TypedDict, Optional, Annotated
import operator


class AgentState(TypedDict):
    """
    그래프 전체에서 공유되는 불변 상태 컨테이너.

    각 노드는 이 State를 읽고, 변경이 필요한 필드만 dict로 반환한다.
    반환된 dict가 기존 State에 merge되어 다음 노드로 전달된다.

    messages 필드만 Annotated[list, operator.add]로 선언하여
    노드가 반환한 리스트를 기존 리스트에 append 방식으로 누적한다.
    나머지 필드는 반환값이 있을 때만 덮어쓴다.
    """

    # ── 대화 이력 ───────────────────────────────────────────
    # operator.add → 노드가 반환한 리스트를 기존 리스트에 누적(append)
    # Checkpointer가 세션별로 이 필드를 영속화함
    messages: Annotated[list, operator.add]

    # ── 입력 ────────────────────────────────────────────────
    user_query: str                   # 원본 사용자 질의 (변경 없음)
    image_data: Optional[dict]        # 멀티모달 이미지 {"images": [base64, ...]}

    # ── 라우팅 결과 ─────────────────────────────────────────
    # router_node가 채운다
    # 단일: {"skill": "data_analytics", "task": "...", "multi_step": false}
    # 멀티: {"multi_step": true, "steps": [{"skill": ..., "task": ...}, ...]}
    routing_plan: dict

    # ── 스킬 실행 추적 ───────────────────────────────────────
    current_skill: str                # 현재/마지막으로 실행된 스킬 이름
    skill_results: dict               # {skill_name: raw_result_dict} 누적

    # ── 출력 ────────────────────────────────────────────────
    final_answer: str                 # 사용자에게 전달될 최종 응답 텍스트

    # ── 오류 및 루프 제어 ────────────────────────────────────
    error: Optional[str]              # 오류 메시지 (없으면 None)
    iteration_count: int              # 재시도 횟수 카운터 (루프 탈출 기준)
