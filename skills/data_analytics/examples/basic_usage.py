"""
Data Analytics Skill 사용 예시
"""

from skills.skill_manager import SkillManager
from datetime import datetime, timedelta


def example_1_calculate_statistics():
    """예시 1: 기간별 통계 계산"""
    print("=" * 60)
    print("예시 1: 기간별 통계 계산")
    print("=" * 60)
    
    manager = SkillManager()
    analytics_skill = manager.get_skill('data_analytics')
    
    # 최근 7일 통계
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    result = analytics_skill.execute('calculate_statistics', {
        'start_date': week_ago.strftime('%Y-%m-%d'),
        'end_date': today.strftime('%Y-%m-%d')
    })
    
    print(f"\n통계 결과:")
    print(f"  - 총 이벤트: {result.get('total_events')}")
    print(f"  - 해결됨: {result.get('resolved')}")
    print(f"  - 미해결: {result.get('unresolved')}")
    print(f"  - 해결률: {result.get('resolution_rate')}%")
    print()


def example_2_find_top_cameras():
    """예시 2: 상위 카메라 찾기"""
    print("=" * 60)
    print("예시 2: 상위 카메라 찾기")
    print("=" * 60)
    
    manager = SkillManager()
    analytics_skill = manager.get_skill('data_analytics')
    
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    result = analytics_skill.execute('find_top_cameras', {
        'start_date': week_ago.strftime('%Y-%m-%d'),
        'end_date': today.strftime('%Y-%m-%d'),
        'limit': 3
    })
    
    print(f"\n상위 카메라:")
    for idx, camera in enumerate(result.get('top_cameras', []), 1):
        print(f"\n{idx}. {camera['camera_name']} ({camera['camera_id']})")
        print(f"   - 총 이벤트: {camera['total_events']}")
        print(f"   - 이벤트 타입: {camera['event_types']}")
    print()


def example_3_analyze_trend():
    """예시 3: 추세 분석"""
    print("=" * 60)
    print("예시 3: 추세 분석")
    print("=" * 60)
    
    manager = SkillManager()
    analytics_skill = manager.get_skill('data_analytics')
    
    today = datetime.now()
    current_start = today - timedelta(days=7)
    current_end = today
    previous_start = today - timedelta(days=14)
    previous_end = today - timedelta(days=7)
    
    result = analytics_skill.execute('analyze_trend', {
        'current_start': current_start.strftime('%Y-%m-%d'),
        'current_end': current_end.strftime('%Y-%m-%d'),
        'previous_start': previous_start.strftime('%Y-%m-%d'),
        'previous_end': previous_end.strftime('%Y-%m-%d')
    })
    
    print(f"\n추세 분석:")
    print(f"  - 현재 기간 이벤트: {result['current_period']['total_events']}")
    print(f"  - 이전 기간 이벤트: {result['previous_period']['total_events']}")
    print(f"  - 변화량: {result['overall_change']}")
    print(f"  - 변화율: {result['overall_change_rate']}%")
    print()


def example_4_assess_risk():
    """예시 4: 위험도 평가"""
    print("=" * 60)
    print("예시 4: 위험도 평가")
    print("=" * 60)
    
    manager = SkillManager()
    analytics_skill = manager.get_skill('data_analytics')
    
    # 전체 시스템 위험도
    result = analytics_skill.execute('assess_risk', {
        'days': 7
    })
    
    print(f"\n위험도 평가:")
    print(f"  - 대상: {result.get('target')}")
    print(f"  - 기간: 최근 {result.get('period_days')}일")
    print(f"  - 총 이벤트: {result.get('total_events')}")
    print(f"  - 미해결 이벤트: {result.get('unresolved_events')}")
    print(f"  - 위험 수준: {result.get('risk_level')}")
    print(f"  - 권고사항: {result.get('recommendation')}")
    print()


def example_5_analyze_query():
    """예시 5: 자연어 쿼리 분석"""
    print("=" * 60)
    print("예시 5: 자연어 쿼리 분석")
    print("=" * 60)
    
    manager = SkillManager()
    analytics_skill = manager.get_skill('data_analytics')
    
    # 자연어로 질문
    result = analytics_skill.execute('analyze_query', {
        'query': '최근 7일간 전체 시스템의 위험도를 평가해주세요'
    })
    
    print(f"\n쿼리: {result.get('query', '최근 7일간 전체 시스템의 위험도를 평가해주세요')}")
    print(f"사용된 도구: {result.get('tool_used')}")
    print(f"\n설명:")
    print(result.get('explanation'))
    print()


def example_6_skill_manager():
    """예시 6: Skill Manager를 통한 실행"""
    print("=" * 60)
    print("예시 6: Skill Manager를 통한 실행")
    print("=" * 60)
    
    manager = SkillManager()
    
    # 사용 가능한 Skills 확인
    print(f"\n사용 가능한 Skills: {manager.list_skills()}")
    
    # Data Analytics Skill 정보
    analytics_skill = manager.get_skill('data_analytics')
    print(f"\nSkill 이름: {analytics_skill.metadata.name}")
    print(f"버전: {analytics_skill.metadata.version}")
    print(f"설명: {analytics_skill.metadata.description}")
    print(f"기능: {analytics_skill.get_capabilities()}")
    
    # Skill Manager를 통한 직접 실행
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    result = manager.execute_skill(
        skill_name='data_analytics',
        task='calculate_statistics',
        context={
            'start_date': week_ago.strftime('%Y-%m-%d'),
            'end_date': today.strftime('%Y-%m-%d')
        }
    )
    
    print(f"\n실행 성공: {result.get('success', True)}")
    print(f"총 이벤트: {result.get('result', result).get('total_events')}")
    print()


if __name__ == "__main__":
    print("\n🚀 Data Analytics Skill 예시 코드\n")
    
    try:
        example_1_calculate_statistics()
        example_2_find_top_cameras()
        example_3_analyze_trend()
        example_4_assess_risk()
        # example_5_analyze_query()  # LLM 호출 필요
        example_6_skill_manager()
        
        print("✅ 모든 예시 실행 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
