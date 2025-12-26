"""
RAG 검색 도구
지식 베이스에서 정보를 검색하는 도구들
"""

from langchain.tools import tool
from utils.rag_system import RAGSystem

# RAG 시스템 전역 인스턴스
_rag_system = None


def get_rag_system() -> RAGSystem:
    """RAG 시스템 싱글톤 인스턴스 반환"""
    global _rag_system
    if _rag_system is None:
        _rag_system = RAGSystem()
        _rag_system.initialize()
    return _rag_system


@tool
def search_knowledge_base(query: str, k: int = 3) -> str:
    """
    지식 베이스에서 관련 정보를 검색합니다.
    안전 규정, 대응 절차, 조치 사항 등을 찾을 수 있습니다.

    Args:
        query: 검색 쿼리 (예: "안전모 미착용 시 조치 방법")
        k: 반환할 결과 수 (기본값: 3)

    Returns:
        검색된 문서 내용
    """
    rag = get_rag_system()
    results = rag.search(query, k=k)

    if not results:
        return "관련 정보를 찾을 수 없습니다."

    # 결과를 텍스트로 포맷팅
    output = []
    for i, doc in enumerate(results, 1):
        event_type = doc.metadata.get('event_type', 'N/A')
        output.append(f"=== 검색 결과 {i} (이벤트 타입: {event_type}) ===")
        output.append(doc.page_content)
        output.append("")

    return "\n".join(output)


@tool
def get_action_guide(event_type: str) -> str:
    """
    특정 이벤트 타입에 대한 조치 가이드를 조회합니다.

    Args:
        event_type: 이벤트 타입 (NO_HELMET, NO_SAFETY_VEST, FALL_DETECTED, RESTRICTED_AREA, EQUIPMENT_MISUSE, FIRE_HAZARD)

    Returns:
        해당 이벤트에 대한 상세 조치 가이드
    """
    rag = get_rag_system()
    guide = rag.get_action_guide(event_type)

    return f"=== {event_type} 조치 가이드 ===\n\n{guide}"


@tool
def search_safety_regulations(query: str) -> str:
    """
    안전 규정 및 법규 정보를 검색합니다.

    Args:
        query: 검색 쿼리 (예: "안전모 착용 관련 법규")

    Returns:
        관련 안전 규정 및 법규 정보
    """
    rag = get_rag_system()
    results = rag.search(query, k=2)

    if not results:
        return "관련 안전 규정을 찾을 수 없습니다."

    # 법규 관련 내용만 추출
    output = ["=== 관련 안전 규정 ===\n"]
    for doc in results:
        content = doc.page_content
        # "관련 법규" 섹션 찾기
        if "관련 법규" in content or "법" in content:
            output.append(content)

    return "\n\n".join(output)