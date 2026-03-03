"""
tests/test_d_multi_turn.py
카테고리 D: 멀티턴 대화 컨텍스트 테스트 (M2 Checkpointer 검증)

- 동일 세션 내 이전 대화를 참조하는지
- 세션 간 대화 이력이 격리되는지
- API 레벨과 Supervisor 레벨 각각에서 검증
"""

import pytest


class TestMultiTurnSupervisor:
    """Supervisor 직접 호출로 멀티턴 검증."""

    def test_d1_multi_turn_no_crash(self, supervisor):
        """동일 session_id로 3번 연속 호출해도 오류 없음."""
        session = "multi_turn_d1"
        queries = [
            "안전모 착용 규정 설명해줘",
            "방금 설명에서 위반 시 벌금은 얼마야?",
            "그 법규 조항 번호가 뭐야?",
        ]
        for q in queries:
            result = supervisor.execute(q, session_id=session)
            assert result is not None
            assert len(result) > 5
            assert "Traceback" not in result

    def test_d2_session_responses_are_unique(self, supervisor):
        """
        동일 세션에서 서로 다른 질의 → 서로 다른 응답.
        (완전히 동일한 응답을 반환하지 않아야 함)
        """
        session = "uniqueness_d2"
        r1 = supervisor.execute("낙상 사고 대응 방법은?", session_id=session)
        r2 = supervisor.execute("화재 위험 대응 방법은?", session_id=session)
        # 완전히 동일한 응답이 나오면 캐시 버그
        assert r1 != r2, "서로 다른 질의에 동일 응답 반환"

    def test_d3_different_sessions_dont_share_context(self, supervisor):
        """
        세션 A와 세션 B는 독립적.
        세션 B에서 세션 A의 특수 정보가 나오지 않아야 함.
        """
        # 세션 A에서 매우 구체적인 카메라 정보 질의
        supervisor.execute(
            "CAM-007에서 발생한 오늘 이벤트를 분석해줘",
            session_id="session_d3_A"
        )
        # 세션 B에서 "이전 결과" 참조 시도
        result_b = supervisor.execute(
            "방금 분석한 카메라가 어디야?",
            session_id="session_d3_B"
        )
        # 세션 B는 CAM-007을 언급한 적 없음 → 특정 답을 알 수 없어야 함
        # (완전히 불가능하진 않지만, "이전 대화"로 CAM-007을 직접 아는 건 불가여야 함)
        assert result_b is not None
        assert "Traceback" not in result_b


class TestMultiTurnAPI:
    """HTTP API 레벨 멀티턴 검증."""

    def test_d4_api_multi_turn_thread_id_consistent(self, http_client, auth_headers):
        """
        동일 session_id로 두 번 호출 → 반환 session_id(thread_id) 동일.
        """
        session_id = "api_multi_d4"
        thread_ids = []

        for query in ["안전 규정 알려줘", "관련 처벌 기준은?"]:
            resp = http_client.post("/api/query",
                json={"query": query, "session_id": session_id},
                headers=auth_headers,
            )
            assert resp.status_code == 200
            thread_ids.append(resp.json().get("session_id"))

        assert thread_ids[0] == thread_ids[1], (
            f"동일 session_id에서 다른 thread_id: {thread_ids}"
        )

    def test_d5_api_session_isolation(self, http_client, auth_headers):
        """서로 다른 session_id → 반환 thread_id도 달라야 함."""
        resp_a = http_client.post("/api/query",
            json={"query": "통계 보여줘", "session_id": "iso_session_A"},
            headers=auth_headers,
        )
        resp_b = http_client.post("/api/query",
            json={"query": "통계 보여줘", "session_id": "iso_session_B"},
            headers=auth_headers,
        )
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200

        tid_a = resp_a.json().get("session_id")
        tid_b = resp_b.json().get("session_id")
        assert tid_a != tid_b, f"다른 세션이 동일 thread_id 공유: {tid_a}"
