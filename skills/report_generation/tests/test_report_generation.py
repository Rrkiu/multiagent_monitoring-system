"""
Report Generation Skill 테스트
"""

import pytest
from skills.report_generation.skill import ReportGenerationSkill


@pytest.fixture
def report_skill():
    """Report Generation Skill 인스턴스"""
    return ReportGenerationSkill()


def test_skill_metadata(report_skill):
    """메타데이터 테스트"""
    assert report_skill.metadata.name == "report_generation"
    assert report_skill.metadata.version == "1.0.0"
    assert "report" in report_skill.metadata.tags
    assert "document" in report_skill.metadata.tags


def test_skill_capabilities(report_skill):
    """기능 목록 테스트"""
    capabilities = report_skill.get_capabilities()
    
    assert "generate_event_report" in capabilities
    assert "generate_statistics_report" in capabilities
    assert "generate_action_plan" in capabilities
    assert "generate_summary" in capabilities
    assert "generate_incident_report" in capabilities
    assert "generate_daily_report" in capabilities
    assert "generate_weekly_report" in capabilities


def test_validate_input_event_report(report_skill):
    """입력 검증 테스트 - 이벤트 보고서"""
    # 유효한 입력
    assert report_skill.validate_input('generate_event_report', {
        'events': [{'id': '1', 'type': 'test'}]
    }) == True
    
    # 무효한 입력 (events 없음)
    assert report_skill.validate_input('generate_event_report', {}) == False


def test_validate_input_statistics_report(report_skill):
    """입력 검증 테스트 - 통계 보고서"""
    # 유효한 입력
    assert report_skill.validate_input('generate_statistics_report', {
        'statistics': {'total': 10}
    }) == True
    
    # 무효한 입력
    assert report_skill.validate_input('generate_statistics_report', {}) == False


def test_validate_input_action_plan(report_skill):
    """입력 검증 테스트 - 조치 방안"""
    # 유효한 입력
    assert report_skill.validate_input('generate_action_plan', {
        'event_data': {'id': '1'}
    }) == True
    
    # 무효한 입력
    assert report_skill.validate_input('generate_action_plan', {}) == False


def test_validate_input_summary(report_skill):
    """입력 검증 테스트 - 요약"""
    # 유효한 입력
    assert report_skill.validate_input('generate_summary', {
        'content': 'Some long content here'
    }) == True
    
    # 무효한 입력
    assert report_skill.validate_input('generate_summary', {}) == False


def test_validate_input_incident_report(report_skill):
    """입력 검증 테스트 - 사고 보고서"""
    # 유효한 입력
    assert report_skill.validate_input('generate_incident_report', {
        'incident_data': {'id': 'INC-001'}
    }) == True
    
    # 무효한 입력
    assert report_skill.validate_input('generate_incident_report', {}) == False


def test_validate_input_daily_report(report_skill):
    """입력 검증 테스트 - 일일 보고서"""
    # 파라미터 선택사항
    assert report_skill.validate_input('generate_daily_report', {}) == True
    assert report_skill.validate_input('generate_daily_report', {
        'date': '2026-02-10'
    }) == True


def test_validate_input_weekly_report(report_skill):
    """입력 검증 테스트 - 주간 보고서"""
    # 파라미터 선택사항
    assert report_skill.validate_input('generate_weekly_report', {}) == True
    assert report_skill.validate_input('generate_weekly_report', {
        'start_date': '2026-02-03',
        'end_date': '2026-02-10'
    }) == True


def test_tools_initialization(report_skill):
    """도구 초기화 테스트"""
    assert 'llm' in report_skill.tools
    assert 'event_report_generator' in report_skill.tools
    assert 'statistics_report_generator' in report_skill.tools
    assert 'action_plan_generator' in report_skill.tools
    assert 'summary_generator' in report_skill.tools
    assert 'incident_report_generator' in report_skill.tools


def test_format_events(report_skill):
    """이벤트 포맷팅 테스트"""
    events = [
        {
            'id': 'EVT-001',
            'event_type': 'NO_HELMET',
            'severity': 'HIGH',
            'camera_id': 'CAM-001',
            'camera_name': '작업장 A',
            'timestamp': '2026-02-10 09:00:00',
            'resolved': False,
            'description': '안전모 미착용'
        }
    ]
    
    formatted = report_skill._format_events(events)
    
    assert 'EVT-001' in formatted
    assert 'NO_HELMET' in formatted
    assert 'HIGH' in formatted
    assert '미해결' in formatted


def test_default_prompts(report_skill):
    """기본 프롬프트 테스트"""
    event_prompt = report_skill._get_default_event_report_prompt()
    assert '{period}' in event_prompt
    assert '{events}' in event_prompt
    
    stats_prompt = report_skill._get_default_statistics_report_prompt()
    assert '{period}' in stats_prompt
    assert '{statistics}' in stats_prompt
    
    action_prompt = report_skill._get_default_action_plan_prompt()
    assert '{event}' in action_prompt
    assert '{knowledge_context}' in action_prompt
    
    incident_prompt = report_skill._get_default_incident_report_prompt()
    assert '{incident}' in incident_prompt
    assert '{analysis}' in incident_prompt


# 통합 테스트 (실제 LLM 호출 필요)
@pytest.mark.skip(reason="Requires LLM API call")
def test_generate_event_report_integration(report_skill):
    """이벤트 보고서 생성 통합 테스트"""
    events = [
        {
            'id': 'EVT-001',
            'event_type': 'NO_HELMET',
            'severity': 'HIGH',
            'camera_id': 'CAM-001',
            'camera_name': '작업장 A',
            'timestamp': '2026-02-10 09:00:00',
            'resolved': False,
            'description': '안전모 미착용'
        }
    ]
    
    result = report_skill.execute('generate_event_report', {
        'events': events,
        'period': '일일'
    })
    
    assert 'report_type' in result
    assert result['report_type'] == 'event_report'
    assert 'report' in result


@pytest.mark.skip(reason="Requires LLM API call")
def test_generate_summary_integration(report_skill):
    """요약 생성 통합 테스트"""
    content = "이것은 긴 내용입니다. " * 50
    
    result = report_skill.execute('generate_summary', {
        'content': content,
        'max_length': 100
    })
    
    assert 'summary' in result
    assert len(result['summary']) <= 150  # 약간의 여유


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
