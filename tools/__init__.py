"""
모든 Tool을 한 곳에서 import할 수 있도록 통합
"""

from tools.data_tools import (
    get_camera_events,
    get_all_cameras,
    get_events_by_type,
    get_events_by_date,
    get_unresolved_events
)

from tools.rag_tools import (
    search_knowledge_base,
    get_action_guide,
    search_safety_regulations
)

from tools.analytics_tools import (
    calculate_statistics,
    find_top_event_camera,
    calculate_trend,
    assess_risk_level
)

from tools.web_search_tools import (
    get_all_web_search_tools,
    create_web_search_tool,
    create_detailed_web_search_tool,
    create_safety_news_tool,
    create_safety_regulations_tool
)

# 모든 Tool 리스트
ALL_TOOLS = [
    # Data Tools
    get_camera_events,
    get_all_cameras,
    get_events_by_type,
    get_events_by_date,
    get_unresolved_events,

    # RAG Tools
    search_knowledge_base,
    get_action_guide,
    search_safety_regulations,

    # Analytics Tools
    calculate_statistics,
    find_top_event_camera,
    calculate_trend,
    assess_risk_level,
]

# 웹 검색 도구는 별도로 관리 (동적 생성)
WEB_SEARCH_TOOLS = get_all_web_search_tools()

__all__ = ["ALL_TOOLS", "WEB_SEARCH_TOOLS"]