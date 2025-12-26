"""
데이터 조회 도구
events.json 파일에서 이벤트 데이터를 조회하는 도구들
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from langchain.tools import tool
from config import settings


def load_events() -> List[Dict]:
    """이벤트 데이터 로드"""
    events_file = Path(settings.events_file)

    if not events_file.exists():
        return []

    with open(events_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_date(date_str: str) -> datetime:
    """
    날짜 문자열을 datetime 객체로 변환
    지원 형식: YYYY-MM-DD, today, yesterday
    """
    date_str = date_str.lower().strip()

    if date_str == "today":
        return datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    elif date_str == "yesterday":
        return (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        return datetime.fromisoformat(date_str)


@tool
def get_camera_events(camera_id: str, start_date: str = None, end_date: str = None) -> str:
    """
    특정 카메라에서 발생한 이벤트 목록을 조회합니다.

    Args:
        camera_id: 카메라 ID (예: CAM-001, CAM-002)
        start_date: 시작 날짜 (YYYY-MM-DD 형식 또는 'today', 'yesterday'). 선택사항.
        end_date: 종료 날짜 (YYYY-MM-DD 형식 또는 'today', 'yesterday'). 선택사항.

    Returns:
        JSON 형식의 이벤트 목록 문자열
    """
    events = load_events()

    # 카메라 ID로 필터링
    filtered = [e for e in events if e['camera_id'] == camera_id]

    # 날짜 필터링
    if start_date:
        start = parse_date(start_date)
        filtered = [e for e in filtered if datetime.fromisoformat(e['timestamp']) >= start]

    if end_date:
        end = parse_date(end_date)
        # 종료일 23:59:59까지 포함
        end = end.replace(hour=23, minute=59, second=59)
        filtered = [e for e in filtered if datetime.fromisoformat(e['timestamp']) <= end]

    if not filtered:
        return f"카메라 {camera_id}에서 해당 기간에 발생한 이벤트가 없습니다."

    # 결과 요약
    result = {
        "camera_id": camera_id,
        "total_events": len(filtered),
        "events": filtered
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_all_cameras() -> str:
    """
    시스템에 등록된 모든 카메라 목록과 각 카메라의 이벤트 수를 조회합니다.

    Returns:
        JSON 형식의 카메라 목록 문자열
    """
    events = load_events()

    # 카메라별 이벤트 집계
    camera_stats = {}
    for event in events:
        cam_id = event['camera_id']
        cam_name = event['camera_name']

        if cam_id not in camera_stats:
            camera_stats[cam_id] = {
                "camera_id": cam_id,
                "camera_name": cam_name,
                "total_events": 0,
                "unresolved_events": 0
            }

        camera_stats[cam_id]["total_events"] += 1
        if not event['resolved']:
            camera_stats[cam_id]["unresolved_events"] += 1

    result = {
        "total_cameras": len(camera_stats),
        "cameras": list(camera_stats.values())
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_events_by_type(event_type: str, start_date: str = None, end_date: str = None) -> str:
    """
    특정 타입의 이벤트 목록을 조회합니다.

    Args:
        event_type: 이벤트 타입 (NO_HELMET, NO_SAFETY_VEST, FALL_DETECTED, RESTRICTED_AREA, EQUIPMENT_MISUSE, FIRE_HAZARD)
        start_date: 시작 날짜 (선택사항)
        end_date: 종료 날짜 (선택사항)

    Returns:
        JSON 형식의 이벤트 목록 문자열
    """
    events = load_events()

    # 이벤트 타입으로 필터링
    filtered = [e for e in events if e['event_type'] == event_type]

    # 날짜 필터링
    if start_date:
        start = parse_date(start_date)
        filtered = [e for e in filtered if datetime.fromisoformat(e['timestamp']) >= start]

    if end_date:
        end = parse_date(end_date)
        end = end.replace(hour=23, minute=59, second=59)
        filtered = [e for e in filtered if datetime.fromisoformat(e['timestamp']) <= end]

    if not filtered:
        return f"{event_type} 타입의 이벤트가 해당 기간에 없습니다."

    result = {
        "event_type": event_type,
        "total_events": len(filtered),
        "events": filtered
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_events_by_date(date: str) -> str:
    """
    특정 날짜에 발생한 모든 이벤트를 조회합니다.

    Args:
        date: 날짜 (YYYY-MM-DD 형식 또는 'today', 'yesterday')

    Returns:
        JSON 형식의 이벤트 목록 문자열
    """
    events = load_events()

    target_date = parse_date(date)
    next_date = target_date + timedelta(days=1)

    # 해당 날짜의 이벤트 필터링
    filtered = [
        e for e in events
        if target_date <= datetime.fromisoformat(e['timestamp']) < next_date
    ]

    if not filtered:
        return f"{date}에 발생한 이벤트가 없습니다."

    # 타입별 집계
    type_counts = {}
    for event in filtered:
        event_type = event['event_type']
        type_counts[event_type] = type_counts.get(event_type, 0) + 1

    result = {
        "date": target_date.strftime('%Y-%m-%d'),
        "total_events": len(filtered),
        "event_type_summary": type_counts,
        "events": filtered
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def get_unresolved_events(severity: str = None) -> str:
    """
    미해결 이벤트 목록을 조회합니다.

    Args:
        severity: 심각도 필터 (LOW, MEDIUM, HIGH, CRITICAL). 선택사항.

    Returns:
        JSON 형식의 미해결 이벤트 목록 문자열
    """
    events = load_events()

    # 미해결 이벤트 필터링
    filtered = [e for e in events if not e['resolved']]

    # 심각도 필터링
    if severity:
        filtered = [e for e in filtered if e['severity'] == severity]

    if not filtered:
        filter_msg = f" (심각도: {severity})" if severity else ""
        return f"미해결 이벤트{filter_msg}가 없습니다."

    # 심각도별 집계
    severity_counts = {}
    for event in filtered:
        sev = event['severity']
        severity_counts[sev] = severity_counts.get(sev, 0) + 1

    result = {
        "total_unresolved": len(filtered),
        "severity_summary": severity_counts,
        "events": filtered
    }

    return json.dumps(result, ensure_ascii=False, indent=2)