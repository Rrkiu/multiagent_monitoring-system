"""
모의 이벤트 데이터 생성 스크립트
실제 작업장 안전 모니터링 시스템에서 발생할 법한 이벤트 데이터를 생성합니다.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

# 카메라 정보
CAMERAS = [
    {"id": "CAM-001", "name": "작업장 A동 입구", "location": "작업장 A동 입구"},
    {"id": "CAM-002", "name": "작업장 B동 중앙", "location": "작업장 B동 중앙"},
    {"id": "CAM-003", "name": "자재 보관소", "location": "자재 보관소"},
    {"id": "CAM-004", "name": "장비 작업 구역", "location": "장비 작업 구역"},
    {"id": "CAM-005", "name": "야외 작업장", "location": "야외 작업장"},
]

# 이벤트 타입 및 설명
EVENT_TYPES = {
    "NO_HELMET": {
        "severity": "MEDIUM",
        "descriptions": [
            "작업자가 안전모를 착용하지 않은 채 작업장에 진입했습니다.",
            "안전모 미착용 상태로 작업 중인 것이 감지되었습니다.",
            "작업 중 안전모를 벗은 것이 포착되었습니다.",
        ]
    },
    "NO_SAFETY_VEST": {
        "severity": "LOW",
        "descriptions": [
            "작업자가 안전조끼를 착용하지 않았습니다.",
            "안전조끼 미착용 상태로 작업장에 출입했습니다.",
            "안전조끼 없이 작업 중인 것이 확인되었습니다.",
        ]
    },
    "FALL_DETECTED": {
        "severity": "HIGH",
        "descriptions": [
            "작업자가 넘어지는 것이 감지되었습니다.",
            "작업 중 추락 사고가 발생했습니다.",
            "바닥에 쓰러진 작업자가 포착되었습니다.",
        ]
    },
    "RESTRICTED_AREA": {
        "severity": "MEDIUM",
        "descriptions": [
            "권한 없는 인원이 제한구역에 출입했습니다.",
            "제한구역 무단 침입이 감지되었습니다.",
            "출입 금지 구역에 사람이 포착되었습니다.",
        ]
    },
    "EQUIPMENT_MISUSE": {
        "severity": "HIGH",
        "descriptions": [
            "장비를 잘못된 방법으로 사용하고 있습니다.",
            "장비 오작동 또는 부적절한 사용이 감지되었습니다.",
            "장비 사용 규정을 위반한 것이 포착되었습니다.",
        ]
    },
    "FIRE_HAZARD": {
        "severity": "CRITICAL",
        "descriptions": [
            "화재 위험 요소가 감지되었습니다.",
            "화기 취급 규정 위반이 포착되었습니다.",
            "인화성 물질 근처에서 화기 사용이 감지되었습니다.",
        ]
    },
}

# 담당자 목록
ASSIGNEES = ["김현수", "이지은", "박민준", "최서연", "정도윤", "강예진"]


def generate_timestamp(start_date, end_date):
    """랜덤 타임스탬프 생성 (주간 작업시간에 집중)"""
    delta = end_date - start_date
    random_days = random.randint(0, delta.days)
    random_date = start_date + timedelta(days=random_days)

    # 작업시간 (09:00 ~ 18:00) 에 80% 집중
    if random.random() < 0.8:
        hour = random.randint(9, 17)
    else:
        hour = random.randint(6, 22)

    minute = random.randint(0, 59)
    second = random.randint(0, 59)

    return random_date.replace(hour=hour, minute=minute, second=second)


def generate_event(event_id, timestamp):
    """단일 이벤트 생성"""
    camera = random.choice(CAMERAS)
    event_type = random.choice(list(EVENT_TYPES.keys()))
    event_info = EVENT_TYPES[event_type]

    # 심각도에 따라 해결 확률 조정
    severity = event_info["severity"]
    if severity == "LOW":
        resolved = random.random() < 0.9  # 90% 해결
    elif severity == "MEDIUM":
        resolved = random.random() < 0.7  # 70% 해결
    elif severity == "HIGH":
        resolved = random.random() < 0.5  # 50% 해결
    else:  # CRITICAL
        resolved = random.random() < 0.4  # 40% 해결

    event = {
        "event_id": event_id,
        "camera_id": camera["id"],
        "camera_name": camera["name"],
        "event_type": event_type,
        "timestamp": timestamp.isoformat(),
        "severity": severity,
        "resolved": resolved,
        "description": random.choice(event_info["descriptions"]),
        "assigned_to": random.choice(ASSIGNEES),
        "location": camera["location"],
        "notes": None
    }

    # 해결된 이벤트에는 노트 추가
    if resolved:
        notes = [
            "조치 완료",
            "작업자 교육 실시 완료",
            "현장 확인 및 조치 완료",
            "경고 조치 후 해결",
            "안전 규정 준수 확인 완료",
        ]
        event["notes"] = random.choice(notes)

    return event


def generate_mock_data(num_events=None, days=14):
    """모의 데이터 생성"""
    print("🎲 모의 이벤트 데이터 생성 시작...\n")

    # 날짜 범위 설정
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)

    # 이벤트 수 자동 계산 (하루 평균 7~12개)
    if num_events is None:
        num_events = random.randint(days * 7, days * 12)

    print(f"생성 설정:")
    print(f"- 기간: {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')}")
    print(f"- 카메라 수: {len(CAMERAS)}개")
    print(f"- 이벤트 타입: {len(EVENT_TYPES)}가지")
    print(f"- 예상 이벤트 수: 약 {num_events}개\n")

    print("카메라 정보:")
    for cam in CAMERAS:
        print(f"  - {cam['id']}: {cam['name']}")
    print()

    # 이벤트 생성
    events = []
    print("이벤트 생성 중... ", end="", flush=True)

    for i in range(num_events):
        timestamp = generate_timestamp(start_date, end_date)
        event_id = f"EVT-{timestamp.strftime('%Y%m%d')}-{i + 1:03d}"
        event = generate_event(event_id, timestamp)
        events.append(event)

        # 진행 표시
        if (i + 1) % 10 == 0:
            print("█", end="", flush=True)

    print(" 100%\n")

    # 타임스탬프 기준으로 정렬
    events.sort(key=lambda x: x["timestamp"])

    # 통계 출력
    print(f"✅ 총 {len(events)}개의 이벤트 생성 완료!\n")

    # 이벤트 타입별 분포
    print("이벤트 타입별 분포:")
    type_counts = {}
    for event in events:
        event_type = event["event_type"]
        type_counts[event_type] = type_counts.get(event_type, 0) + 1

    for event_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / len(events)) * 100
        print(f"  - {event_type}: {count}건 ({percentage:.1f}%)")

    # 심각도별 분포
    print("\n심각도별 분포:")
    severity_counts = {}
    for event in events:
        severity = event["severity"]
        severity_counts[severity] = severity_counts.get(severity, 0) + 1

    severity_order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    for severity in severity_order:
        count = severity_counts.get(severity, 0)
        percentage = (count / len(events)) * 100
        print(f"  - {severity}: {count}건 ({percentage:.1f}%)")

    # 해결 상태
    resolved_count = sum(1 for e in events if e["resolved"])
    unresolved_count = len(events) - resolved_count
    print(f"\n해결 상태:")
    print(f"  - 해결됨: {resolved_count}건 ({resolved_count / len(events) * 100:.1f}%)")
    print(f"  - 미해결: {unresolved_count}건 ({unresolved_count / len(events) * 100:.1f}%)")

    return events


def save_events(events, filepath="data/events.json"):
    """이벤트 데이터를 JSON 파일로 저장"""
    # 디렉토리가 없으면 생성
    Path(filepath).parent.mkdir(parents=True, exist_ok=True)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print(f"\n💾 데이터가 {filepath}에 저장되었습니다.")


def main():
    """메인 실행 함수"""
    # 데이터 생성
    events = generate_mock_data(days=14)

    # 파일 저장
    save_events(events)

    print("\n" + "=" * 50)
    print("✨ 모의 데이터 생성 완료!")
    print("=" * 50)


if __name__ == "__main__":
    main()