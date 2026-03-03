"""
Data Analytics Skill 테스트
"""

import pytest
from datetime import datetime, timedelta
from skills.data_analytics.skill import DataAnalyticsSkill


@pytest.fixture
def analytics_skill():
    """Data Analytics Skill 인스턴스"""
    return DataAnalyticsSkill()


def test_skill_metadata(analytics_skill):
    """메타데이터 테스트"""
    assert analytics_skill.metadata.name == "data_analytics"
    assert analytics_skill.metadata.version == "1.0.0"
    assert "analytics" in analytics_skill.metadata.tags
    assert "statistics" in analytics_skill.metadata.tags


def test_skill_capabilities(analytics_skill):
    """기능 목록 테스트"""
    capabilities = analytics_skill.get_capabilities()
    
    assert "calculate_statistics" in capabilities
    assert "analyze_trend" in capabilities
    assert "assess_risk" in capabilities
    assert "find_top_cameras" in capabilities
    assert "analyze_query" in capabilities


def test_validate_input_statistics(analytics_skill):
    """입력 검증 테스트 - 통계 계산"""
    # 유효한 입력
    assert analytics_skill.validate_input('calculate_statistics', {
        'start_date': '2025-01-01',
        'end_date': '2025-01-07'
    }) == True
    
    # 무효한 입력 (end_date 없음)
    assert analytics_skill.validate_input('calculate_statistics', {
        'start_date': '2025-01-01'
    }) == False


def test_validate_input_trend(analytics_skill):
    """입력 검증 테스트 - 추세 분석"""
    # 유효한 입력
    valid_context = {
        'current_start': '2025-01-08',
        'current_end': '2025-01-14',
        'previous_start': '2025-01-01',
        'previous_end': '2025-01-07'
    }
    assert analytics_skill.validate_input('analyze_trend', valid_context) == True
    
    # 무효한 입력 (previous_end 없음)
    invalid_context = {
        'current_start': '2025-01-08',
        'current_end': '2025-01-14',
        'previous_start': '2025-01-01'
    }
    assert analytics_skill.validate_input('analyze_trend', invalid_context) == False


def test_validate_input_risk(analytics_skill):
    """입력 검증 테스트 - 위험도 평가"""
    # days는 선택사항이므로 항상 True
    assert analytics_skill.validate_input('assess_risk', {}) == True
    assert analytics_skill.validate_input('assess_risk', {'days': 7}) == True
    assert analytics_skill.validate_input('assess_risk', {
        'camera_id': 'CAM-001',
        'days': 7
    }) == True


def test_validate_input_query(analytics_skill):
    """입력 검증 테스트 - 쿼리 분석"""
    # 유효한 입력
    assert analytics_skill.validate_input('analyze_query', {
        'query': '최근 7일 통계를 보여주세요'
    }) == True
    
    # 무효한 입력 (query 없음)
    assert analytics_skill.validate_input('analyze_query', {}) == False


def test_get_current_date_info(analytics_skill):
    """날짜 정보 생성 테스트"""
    date_info = analytics_skill._get_current_date_info()
    
    assert '오늘 날짜:' in date_info
    assert '어제 날짜:' in date_info
    assert '7일 전:' in date_info
    assert '14일 전:' in date_info
    assert '30일 전:' in date_info


def test_get_risk_recommendation(analytics_skill):
    """위험도 권고사항 테스트"""
    assert '양호' in analytics_skill._get_risk_recommendation('LOW')
    assert '주의' in analytics_skill._get_risk_recommendation('MEDIUM')
    assert '즉시' in analytics_skill._get_risk_recommendation('HIGH')
    assert '긴급' in analytics_skill._get_risk_recommendation('CRITICAL')


def test_tools_initialization(analytics_skill):
    """도구 초기화 테스트"""
    assert 'llm' in analytics_skill.tools
    assert 'statistics_calculator' in analytics_skill.tools
    assert 'trend_analyzer' in analytics_skill.tools
    assert 'risk_assessor' in analytics_skill.tools
    assert 'top_camera_finder' in analytics_skill.tools


# 통합 테스트 (실제 데이터 필요)
@pytest.mark.skip(reason="Requires actual event data")
def test_calculate_statistics_integration(analytics_skill):
    """통계 계산 통합 테스트"""
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    result = analytics_skill.execute('calculate_statistics', {
        'start_date': week_ago.strftime('%Y-%m-%d'),
        'end_date': today.strftime('%Y-%m-%d')
    })
    
    assert 'total_events' in result
    assert 'resolved' in result
    assert 'unresolved' in result
    assert 'resolution_rate' in result


@pytest.mark.skip(reason="Requires actual event data")
def test_find_top_cameras_integration(analytics_skill):
    """상위 카메라 찾기 통합 테스트"""
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    
    result = analytics_skill.execute('find_top_cameras', {
        'start_date': week_ago.strftime('%Y-%m-%d'),
        'end_date': today.strftime('%Y-%m-%d'),
        'limit': 3
    })
    
    assert 'top_cameras' in result or 'error' in result


@pytest.mark.skip(reason="Requires actual event data")
def test_assess_risk_integration(analytics_skill):
    """위험도 평가 통합 테스트"""
    result = analytics_skill.execute('assess_risk', {
        'days': 7
    })
    
    if 'error' not in result:
        assert 'risk_level' in result
        assert result['risk_level'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        assert 'recommendation' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
