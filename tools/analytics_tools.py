"""
분석 도구
이벤트 데이터를 분석하여 통계 및 인사이트를 제공하는 도구들
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List
from collections import Counter

from langchain.tools import tool
from tools.data_tools import load_events, parse_date


@tool
def calculate_statistics(start_date: str, end_date: str) -> str:
    """
    특정 기간의 이벤트 통계를 계산합니다.

    Args:
        start_date: 시작 날짜 (YYYY-MM-DD 또는 'today', 'yesterday')
        end_date: 종료 날짜 (YYYY-MM-DD 또는 'today', 'yesterday')

    Returns:
        JSON 형식의 통계 정보
    """
    events = load_events()

    start = parse_date(start_date)
    end = parse_date(end_date).replace(hour=23, minute=59, second=59)

    # 기간 내 이벤트 필터링
    filtered = [
        e for e in events
        if start <= datetime.fromisoformat(e['timestamp']) <= end
    ]

    if not filtered:
        return "해당 기간에 발생한 이벤트가 없습니다."

    # 통계 계산
    total_events = len(filtered)
    resolved = sum(1 for e in filtered if e['resolved'])
    unresolved = total_events - resolved

    # 타입별 집계
    type_counts = Counter(e['event_type'] for e in filtered)

    # 심각도별 집계
    severity_counts = Counter(e['severity'] for e in filtered)

    # 카메라별 집계
    camera_counts = Counter(e['camera_id'] for e in filtered)

    result = {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "total_events": total_events,
        "resolved": resolved,
        "unresolved": unresolved,
        "resolution_rate": round(resolved / total_events * 100, 2) if total_events > 0 else 0,
        "by_event_type": dict(type_counts),
        "by_severity": dict(severity_counts),
        "by_camera": dict(camera_counts)
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def find_top_event_camera(start_date: str, end_date: str, limit: int = 3) -> str:
    """
    특정 기간 동안 가장 많은 이벤트가 발생한 카메라를 찾습니다.

    Args:
        start_date: 시작 날짜
        end_date: 종료 날짜
        limit: 반환할 카메라 수 (기본값: 3)

    Returns:
        JSON 형식의 상위 카메라 목록
    """
    events = load_events()

    start = parse_date(start_date)
    end = parse_date(end_date).replace(hour=23, minute=59, second=59)

    # 기간 내 이벤트 필터링
    filtered = [
        e for e in events
        if start <= datetime.fromisoformat(e['timestamp']) <= end
    ]

    if not filtered:
        return "해당 기간에 발생한 이벤트가 없습니다."

    # 카메라별 집계
    camera_stats = {}
    for event in filtered:
        cam_id = event['camera_id']
        cam_name = event['camera_name']

        if cam_id not in camera_stats:
            camera_stats[cam_id] = {
                "camera_id": cam_id,
                "camera_name": cam_name,
                "total_events": 0,
                "event_types": Counter()
            }

        camera_stats[cam_id]["total_events"] += 1
        camera_stats[cam_id]["event_types"][event['event_type']] += 1

    # 이벤트 수로 정렬
    sorted_cameras = sorted(
        camera_stats.values(),
        key=lambda x: x["total_events"],
        reverse=True
    )[:limit]

    # Counter를 dict로 변환
    for cam in sorted_cameras:
        cam["event_types"] = dict(cam["event_types"])

    result = {
        "period": {
            "start_date": start_date,
            "end_date": end_date
        },
        "top_cameras": sorted_cameras
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def calculate_trend(current_start: str, current_end: str, previous_start: str, previous_end: str) -> str:
    """
    두 기간을 비교하여 이벤트 증감 추세를 분석합니다.

    Args:
        current_start: 현재 기간 시작일
        current_end: 현재 기간 종료일
        previous_start: 이전 기간 시작일
        previous_end: 이전 기간 종료일

    Returns:
        JSON 형식의 추세 분석 결과
    """
    events = load_events()

    # 현재 기간
    curr_start = parse_date(current_start)
    curr_end = parse_date(current_end).replace(hour=23, minute=59, second=59)
    current_events = [
        e for e in events
        if curr_start <= datetime.fromisoformat(e['timestamp']) <= curr_end
    ]

    # 이전 기간
    prev_start = parse_date(previous_start)
    prev_end = parse_date(previous_end).replace(hour=23, minute=59, second=59)
    previous_events = [
        e for e in events
        if prev_start <= datetime.fromisoformat(e['timestamp']) <= prev_end
    ]

    curr_count = len(current_events)
    prev_count = len(previous_events)

    # 증감률 계산
    if prev_count > 0:
        change_rate = round((curr_count - prev_count) / prev_count * 100, 2)
    else:
        change_rate = 100.0 if curr_count > 0 else 0.0

    # 타입별 증감
    curr_types = Counter(e['event_type'] for e in current_events)
    prev_types = Counter(e['event_type'] for e in previous_events)

    type_changes = {}
    all_types = set(curr_types.keys()) | set(prev_types.keys())

    for event_type in all_types:
        curr = curr_types.get(event_type, 0)
        prev = prev_types.get(event_type, 0)

        if prev > 0:
            rate = round((curr - prev) / prev * 100, 2)
        else:
            rate = 100.0 if curr > 0 else 0.0

        type_changes[event_type] = {
            "current": curr,
            "previous": prev,
            "change": curr - prev,
            "change_rate": rate
        }

    result = {
        "current_period": {
            "start": current_start,
            "end": current_end,
            "total_events": curr_count
        },
        "previous_period": {
            "start": previous_start,
            "end": previous_end,
            "total_events": prev_count
        },
        "overall_change": curr_count - prev_count,
        "overall_change_rate": change_rate,
        "by_event_type": type_changes
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


@tool
def assess_risk_level(camera_id: str = None, days: int = 7) -> str:
    """
    특정 카메라 또는 전체 시스템의 위험도를 평가합니다.

    Args:
        camera_id: 카메라 ID (선택사항, 없으면 전체 평가)
        days: 평가 기간 (일 수, 기본값: 7일)

    Returns:
        JSON 형식의 위험도 평가 결과
    """
    events = load_events()

    # 기간 설정
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 필터링
    filtered = [
        e for e in events
        if start_date <= datetime.fromisoformat(e['timestamp']) <= end_date
    ]

    if camera_id:
        filtered = [e for e in filtered if e['camera_id'] == camera_id]

    if not filtered:
        target = f"카메라 {camera_id}" if camera_id else "시스템"
        return f"{target}에서 최근 {days}일간 발생한 이벤트가 없습니다."

    # 위험도 점수 계산
    severity_scores = {
        "LOW": 1,
        "MEDIUM": 3,
        "HIGH": 7,
        "CRITICAL": 10
    }

    total_score = sum(severity_scores.get(e['severity'], 0) for e in filtered)
    avg_score = total_score / len(filtered)

    # 미해결 이벤트
    unresolved = [e for e in filtered if not e['resolved']]
    critical_unresolved = [e for e in unresolved if e['severity'] == 'CRITICAL']

    # 위험 수준 결정
    if critical_unresolved or avg_score >= 7:
        risk_level = "CRITICAL"
    elif avg_score >= 5 or len(unresolved) > len(filtered) * 0.5:
        risk_level = "HIGH"
    elif avg_score >= 3:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    result = {
        "target": camera_id if camera_id else "전체 시스템",
        "period_days": days,
        "total_events": len(filtered),
        "unresolved_events": len(unresolved),
        "critical_unresolved": len(critical_unresolved),
        "average_severity_score": round(avg_score, 2),
        "risk_level": risk_level,
        "recommendation": _get_risk_recommendation(risk_level)
    }

    return json.dumps(result, ensure_ascii=False, indent=2)


def _get_risk_recommendation(risk_level: str) -> str:
    """위험 수준에 따른 권장 사항"""
    recommendations = {
        "LOW": "현재 안전 수준이 양호합니다. 정기적인 모니터링을 계속하세요.",
        "MEDIUM": "주의가 필요합니다. 미해결 이벤트를 우선 처리하고 안전 교육을 강화하세요.",
        "HIGH": "즉시 조치가 필요합니다. 모든 미해결 이벤트를 긴급 점검하고 안전 관리자 회의를 소집하세요.",
        "CRITICAL": "긴급 상황입니다. 즉시 현장 작업을 중단하고 전체 안전 점검을 실시하세요."
    }
    return recommendations.get(risk_level, "평가 불가")