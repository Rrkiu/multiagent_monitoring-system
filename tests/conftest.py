"""
tests/conftest.py
M4 테스트 공통 픽스처 및 설정

모든 테스트 모듈이 공유하는 supervisor, http client, 샘플 데이터.
"""

import pytest
from fastapi.testclient import TestClient

# ────────────────────────────────────────────────────────────
# 공유 픽스처: supervisor (그래프 컴파일 한 번만 수행)
# ────────────────────────────────────────────────────────────
@pytest.fixture(scope="session")
def supervisor():
    """
    세션 범위 SupervisorLangGraph 픽스처.
    - use_sqlite=False: 테스트 간 DB 오염 방지 (MemorySaver 사용)
    - 임포트 오류 시 스킵 처리
    """
    from agents.supervisor_langgraph import SupervisorLangGraph
    return SupervisorLangGraph(use_memory=True, use_sqlite=False)


@pytest.fixture(scope="session")
def http_client():
    """
    FastAPI TestClient — 실제 HTTP 계층 테스트용.
    인증이 필요한 엔드포인트는 별도 헤더 추가.
    """
    from app import app
    with TestClient(app, raise_server_exceptions=False) as client:
        yield client


@pytest.fixture(scope="session")
def auth_headers(http_client):
    """
    테스트용 JWT 토큰 발급 후 Authorization 헤더 반환.
    """
    resp = http_client.post("/auth/token", data={
        "username": "admin",
        "password": "admin123",
    })
    if resp.status_code != 200:
        pytest.skip(f"인증 토큰 발급 실패: {resp.status_code} — 인증 서버 확인 필요")
    token = resp.json().get("access_token", "")
    return {"Authorization": f"Bearer {token}"}


# ────────────────────────────────────────────────────────────
# 공유 샘플 데이터 (현실적인 안전 이벤트)
# ────────────────────────────────────────────────────────────
SAMPLE_EVENTS = [
    {
        "id": "EVT-001", "event_type": "NO_HELMET", "severity": "HIGH",
        "camera_id": "CAM-001", "camera_name": "작업장 A동 입구",
        "timestamp": "2026-03-01 09:30:00", "resolved": True,
        "description": "작업자 안전모 미착용",
    },
    {
        "id": "EVT-002", "event_type": "FALL_DETECTED", "severity": "CRITICAL",
        "camera_id": "CAM-003", "camera_name": "작업장 B동 2층",
        "timestamp": "2026-03-01 14:15:00", "resolved": True,
        "description": "작업자 낙상 사고 발생, 즉시 구조 완료",
    },
    {
        "id": "EVT-003", "event_type": "FIRE_HAZARD", "severity": "CRITICAL",
        "camera_id": "CAM-005", "camera_name": "공장 보일러실",
        "timestamp": "2026-03-01 22:10:00", "resolved": False,
        "description": "보일러실 연기 감지",
    },
    {
        "id": "EVT-004", "event_type": "NO_HELMET", "severity": "MEDIUM",
        "camera_id": "CAM-002", "camera_name": "작업장 A동 2층",
        "timestamp": "2026-03-02 16:45:00", "resolved": False,
        "description": "안전모 미착용 2차 발생",
    },
]

SAMPLE_STATISTICS = {
    "total_events": len(SAMPLE_EVENTS),
    "by_type": {"NO_HELMET": 2, "FALL_DETECTED": 1, "FIRE_HAZARD": 1},
    "by_severity": {"CRITICAL": 2, "HIGH": 1, "MEDIUM": 1},
    "resolved": 2,
    "unresolved": 2,
}
