"""
Report Generation Skill 사용 예시
"""

from skills.skill_manager import SkillManager
from datetime import datetime, timedelta


def example_1_event_report():
    """예시 1: 이벤트 보고서 생성"""
    print("=" * 60)
    print("예시 1: 이벤트 보고서 생성")
    print("=" * 60)
    
    manager = SkillManager()
    report_skill = manager.get_skill('report_generation')
    
    # 샘플 이벤트 데이터
    sample_events = [
        {
            "id": "EVT-001",
            "event_type": "NO_HELMET",
            "severity": "HIGH",
            "camera_id": "CAM-001",
            "camera_name": "작업장 A동 입구",
            "timestamp": "2026-02-10 09:30:00",
            "resolved": False,
            "description": "작업자가 안전모 미착용 상태로 작업장 진입"
        },
        {
            "id": "EVT-002",
            "event_type": "FALL_DETECTED",
            "severity": "CRITICAL",
            "camera_id": "CAM-003",
            "camera_name": "작업장 B동 2층",
            "timestamp": "2026-02-10 14:15:00",
            "resolved": True,
            "description": "작업자 낙상 사고 발생, 즉시 구조 완료"
        }
    ]
    
    result = report_skill.execute('generate_event_report', {
        'events': sample_events,
        'period': '일일'
    })
    
    print(f"\n보고서 타입: {result.get('report_type')}")
    print(f"기간: {result.get('period')}")
    print(f"총 이벤트: {result.get('total_events')}")
    print(f"\n{result.get('report')}")
    print()


def example_2_statistics_report():
    """예시 2: 통계 보고서 생성"""
    print("=" * 60)
    print("예시 2: 통계 보고서 생성")
    print("=" * 60)
    
    manager = SkillManager()
    report_skill = manager.get_skill('report_generation')
    
    # 샘플 통계 데이터
    sample_statistics = {
        "period": {
            "start_date": "2026-02-03",
            "end_date": "2026-02-10"
        },
        "total_events": 25,
        "resolved": 20,
        "unresolved": 5,
        "resolution_rate": 80.0,
        "by_event_type": {
            "NO_HELMET": 10,
            "NO_SAFETY_VEST": 5,
            "FALL_DETECTED": 3,
            "RESTRICTED_AREA": 7
        },
        "by_severity": {
            "LOW": 8,
            "MEDIUM": 12,
            "HIGH": 4,
            "CRITICAL": 1
        }
    }
    
    result = report_skill.execute('generate_statistics_report', {
        'statistics': sample_statistics,
        'period': '주간'
    })
    
    print(f"\n보고서 타입: {result.get('report_type')}")
    print(f"\n{result.get('report')}")
    print()


def example_3_action_plan():
    """예시 3: 조치 방안 생성"""
    print("=" * 60)
    print("예시 3: 조치 방안 생성")
    print("=" * 60)
    
    manager = SkillManager()
    report_skill = manager.get_skill('report_generation')
    
    # 샘플 이벤트 데이터
    event_data = {
        "id": "EVT-001",
        "event_type": "NO_HELMET",
        "severity": "HIGH",
        "camera_id": "CAM-001",
        "timestamp": "2026-02-10 09:30:00",
        "description": "작업자가 안전모 미착용 상태로 작업장 진입"
    }
    
    knowledge_context = """
안전모 착용 관련 법규:
- 산업안전보건법 제38조: 사업주는 근로자에게 안전모를 지급하고 착용하도록 해야 함
- 위반 시 과태료: 500만원 이하

조치 방법:
1. 즉시 작업 중단
2. 안전모 착용 확인
3. 안전 교육 실시
"""
    
    result = report_skill.execute('generate_action_plan', {
        'event_data': event_data,
        'knowledge_context': knowledge_context
    })
    
    print(f"\n보고서 타입: {result.get('report_type')}")
    print(f"이벤트 타입: {result.get('event_type')}")
    print(f"\n{result.get('action_plan')}")
    print()


def example_4_summary():
    """예시 4: 요약 생성"""
    print("=" * 60)
    print("예시 4: 요약 생성")
    print("=" * 60)
    
    manager = SkillManager()
    report_skill = manager.get_skill('report_generation')
    
    long_content = """
2026년 2월 10일 작업장 A동에서 중대한 안전 사고가 발생했습니다. 
오전 9시 30분경 작업자 김철수씨가 안전모를 착용하지 않은 채 작업장에 진입하여 
작업을 시작했습니다. 이는 산업안전보건법 제38조를 위반한 것으로, 
즉각적인 조치가 필요한 상황입니다. 현장 관리자는 작업을 즉시 중단시키고 
안전모 착용을 지시했으며, 해당 작업자에게 안전 교육을 실시했습니다.
이번 사고를 계기로 작업장 출입 시 안전 장비 착용 여부를 확인하는 
체크리스트 시스템을 도입하기로 결정했습니다.
"""
    
    result = report_skill.execute('generate_summary', {
        'content': long_content,
        'max_length': 100
    })
    
    print(f"\n원본 길이: {result.get('original_length')}자")
    print(f"요약 길이: {result.get('summary_length')}자")
    print(f"\n요약:\n{result.get('summary')}")
    print()


def example_5_daily_report():
    """예시 5: 일일 보고서 생성"""
    print("=" * 60)
    print("예시 5: 일일 보고서 생성")
    print("=" * 60)
    
    manager = SkillManager()
    report_skill = manager.get_skill('report_generation')
    
    # 샘플 데이터
    sample_events = [
        {
            "id": "EVT-001",
            "event_type": "NO_HELMET",
            "severity": "HIGH",
            "camera_id": "CAM-001",
            "camera_name": "작업장 A동",
            "timestamp": "2026-02-10 09:30:00",
            "resolved": True,
            "description": "안전모 미착용"
        }
    ]
    
    sample_statistics = {
        "total_events": 1,
        "resolved": 1,
        "unresolved": 0,
        "resolution_rate": 100.0
    }
    
    result = report_skill.execute('generate_daily_report', {
        'date': '2026-02-10',
        'events': sample_events,
        'statistics': sample_statistics
    })
    
    print(f"\n보고서 타입: {result.get('report_type')}")
    print(f"날짜: {result.get('date')}")
    print(f"\n{result.get('report')}")
    print()


def example_6_skill_manager():
    """예시 6: Skill Manager를 통한 실행"""
    print("=" * 60)
    print("예시 6: Skill Manager를 통한 실행")
    print("=" * 60)
    
    manager = SkillManager()
    
    # 사용 가능한 Skills 확인
    print(f"\n사용 가능한 Skills: {manager.list_skills()}")
    
    # Report Generation Skill 정보
    report_skill = manager.get_skill('report_generation')
    print(f"\nSkill 이름: {report_skill.metadata.name}")
    print(f"버전: {report_skill.metadata.version}")
    print(f"설명: {report_skill.metadata.description}")
    print(f"기능: {report_skill.get_capabilities()}")
    print()


if __name__ == "__main__":
    print("\n🚀 Report Generation Skill 예시 코드\n")
    
    try:
        # example_1_event_report()  # LLM 호출 필요
        # example_2_statistics_report()  # LLM 호출 필요
        # example_3_action_plan()  # LLM 호출 필요
        # example_4_summary()  # LLM 호출 필요
        # example_5_daily_report()  # LLM 호출 필요
        example_6_skill_manager()
        
        print("✅ 모든 예시 실행 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
