"""
utils/session_manager.py
세션 TTL 기반 thread_id 관리

- 사용자별로 thread_id를 발급하여 LangGraph Checkpointer와 연결
- 마지막 활동 기준 2시간 초과 시 새 thread_id 발급 (새 대화 컨텍스트 시작)
- 인메모리 관리 (프로세스 재시작 시 초기화 → 신규 세션으로 시작됨)
"""

import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional

# 세션 TTL: 2시간 (마지막 활동 기준)
SESSION_TTL_MINUTES = 120


class SessionManager:
    """
    사용자 ID → thread_id 매핑 및 TTL 관리

    LangGraph의 Checkpointer는 thread_id를 키로 대화 이력을 저장한다.
    동일한 thread_id → 이전 대화 이력에 이어서 응답
    새 thread_id → 새로운 대화 시작 (이전 이력 없음)

    TTL 만료 시 새 thread_id를 발급하여 자동으로 새 대화를 시작한다.
    """

    def __init__(self):
        # {user_id: {"thread_id": str, "last_active": datetime}}
        self._sessions: Dict[str, dict] = {}

    def get_thread_id(self, user_id: str) -> str:
        """
        사용자 ID에 대응하는 thread_id 반환.
        - 세션이 없으면 신규 발급
        - 세션이 있고 TTL 미만이면 기존 thread_id 반환 (대화 이력 유지)
        - 세션이 있고 TTL 초과면 새 thread_id 발급 (대화 이력 초기화)

        Args:
            user_id: 사용자 식별자 (JWT subject, session cookie 등)

        Returns:
            Checkpointer에 전달할 thread_id
        """
        now = datetime.utcnow()
        session = self._sessions.get(user_id)

        if session is None:
            # 첫 요청 → 신규 세션 발급
            thread_id = self._new_thread_id(user_id)
            self._sessions[user_id] = {
                "thread_id": thread_id,
                "last_active": now,
                "created_at": now,
            }
            print(f"[SessionManager] 신규 세션 발급: {user_id} → {thread_id}")
            return thread_id

        # TTL 만료 체크
        elapsed = now - session["last_active"]
        if elapsed > timedelta(minutes=SESSION_TTL_MINUTES):
            # TTL 초과 → 새 thread_id (이전 Checkpointer 이력은 DB에 남지만 연결 끊김)
            old_thread = session["thread_id"]
            thread_id = self._new_thread_id(user_id)
            session["thread_id"] = thread_id
            session["created_at"] = now
            print(
                f"[SessionManager] TTL 만료({elapsed.seconds // 60}분) → "
                f"새 세션: {user_id} | {old_thread} → {thread_id}"
            )
        else:
            thread_id = session["thread_id"]

        # last_active 갱신
        session["last_active"] = now
        return thread_id

    def reset_session(self, user_id: str) -> str:
        """
        사용자 세션을 강제 초기화 (새 thread_id 발급).
        예: 사용자가 '대화 초기화' 버튼을 눌렀을 때.

        Returns:
            새로 발급된 thread_id
        """
        now = datetime.utcnow()
        thread_id = self._new_thread_id(user_id)
        self._sessions[user_id] = {
            "thread_id": thread_id,
            "last_active": now,
            "created_at": now,
        }
        print(f"[SessionManager] 세션 강제 초기화: {user_id} → {thread_id}")
        return thread_id

    def get_session_info(self, user_id: str) -> Optional[dict]:
        """디버깅용: 세션 정보 반환"""
        session = self._sessions.get(user_id)
        if not session:
            return None
        now = datetime.utcnow()
        elapsed = now - session["last_active"]
        remaining = timedelta(minutes=SESSION_TTL_MINUTES) - elapsed
        return {
            "user_id": user_id,
            "thread_id": session["thread_id"],
            "last_active": session["last_active"].isoformat(),
            "ttl_remaining_minutes": max(0, int(remaining.total_seconds() // 60)),
            "expired": elapsed > timedelta(minutes=SESSION_TTL_MINUTES),
        }

    def cleanup_expired(self) -> int:
        """
        만료된 세션 메모리에서 제거 (정기적으로 호출 가능).
        Returns: 제거된 세션 수
        """
        now = datetime.utcnow()
        expired = [
            uid for uid, s in self._sessions.items()
            if now - s["last_active"] > timedelta(minutes=SESSION_TTL_MINUTES * 2)
        ]
        for uid in expired:
            del self._sessions[uid]
        if expired:
            print(f"[SessionManager] 만료 세션 {len(expired)}개 제거")
        return len(expired)

    @staticmethod
    def _new_thread_id(user_id: str) -> str:
        """user_id + 짧은 UUID로 thread_id 생성"""
        return f"{user_id}_{uuid.uuid4().hex[:8]}"


# ───────────────────────────────────────────────
# 전역 싱글톤 (app.py에서 import하여 공유)
# ───────────────────────────────────────────────
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
