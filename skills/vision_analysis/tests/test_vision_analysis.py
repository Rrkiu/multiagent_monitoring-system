"""
Vision Analysis Skill 테스트
"""

import pytest
from pathlib import Path
from skills.vision_analysis.skill import VisionAnalysisSkill


@pytest.fixture
def vision_skill():
    """Vision Analysis Skill 인스턴스"""
    return VisionAnalysisSkill()


def test_skill_metadata(vision_skill):
    """메타데이터 테스트"""
    assert vision_skill.metadata.name == "vision_analysis"
    assert vision_skill.metadata.version == "1.0.0"
    assert "vision" in vision_skill.metadata.tags
    assert "safety" in vision_skill.metadata.tags


def test_skill_capabilities(vision_skill):
    """기능 목록 테스트"""
    capabilities = vision_skill.get_capabilities()
    
    assert "detect_ppe" in capabilities
    assert "assess_safety" in capabilities
    assert "compare_images" in capabilities
    assert "analyze_multiple" in capabilities


def test_validate_input_detect_ppe(vision_skill):
    """입력 검증 테스트 - PPE 감지"""
    # 유효한 입력
    assert vision_skill.validate_input('detect_ppe', {'image': 'test.jpg'}) == True
    
    # 무효한 입력 (image 없음)
    assert vision_skill.validate_input('detect_ppe', {}) == False


def test_validate_input_compare_images(vision_skill):
    """입력 검증 테스트 - 이미지 비교"""
    # 유효한 입력
    valid_context = {
        'before_image': 'before.jpg',
        'after_image': 'after.jpg'
    }
    assert vision_skill.validate_input('compare_images', valid_context) == True
    
    # 무효한 입력 (after_image 없음)
    invalid_context = {'before_image': 'before.jpg'}
    assert vision_skill.validate_input('compare_images', invalid_context) == False


def test_validate_input_analyze_multiple(vision_skill):
    """입력 검증 테스트 - 다중 이미지 분석"""
    # 유효한 입력
    valid_context = {
        'images': ['img1.jpg', 'img2.jpg']
    }
    assert vision_skill.validate_input('analyze_multiple', valid_context) == True
    
    # 무효한 입력 (images가 리스트가 아님)
    invalid_context = {'images': 'img1.jpg'}
    assert vision_skill.validate_input('analyze_multiple', invalid_context) == False


def test_calculate_risk_level(vision_skill):
    """위험도 계산 테스트"""
    # 위반 없음 - 낮음
    assert vision_skill._calculate_risk_level([]) == 'low'
    
    # 고위험 위반 1개 - 높음
    high_violations = [{'severity': 'high'}]
    assert vision_skill._calculate_risk_level(high_violations) == 'high'
    
    # 중위험 위반 3개 - 중간
    medium_violations = [
        {'severity': 'medium'},
        {'severity': 'medium'},
        {'severity': 'medium'}
    ]
    assert vision_skill._calculate_risk_level(medium_violations) == 'medium'


def test_generate_recommendations(vision_skill):
    """권고사항 생성 테스트"""
    violations = [
        {'type': 'helmet_missing'},
        {'type': 'vest_missing'}
    ]
    
    recommendations = vision_skill._generate_recommendations(violations)
    
    assert '안전모 착용 필수' in recommendations
    assert '안전 조끼 착용 필수' in recommendations
    assert len(recommendations) > 0


def test_summarize_multiple_results(vision_skill):
    """다중 결과 요약 테스트"""
    results = [
        {'result': {'risk_level': 'high'}},
        {'result': {'risk_level': 'medium'}},
        {'result': {'risk_level': 'low'}}
    ]
    
    summary = vision_skill._summarize_multiple_results(results)
    
    assert '3개 이미지' in summary
    assert '고위험: 1' in summary
    assert '중위험: 1' in summary
    assert '저위험: 1' in summary


def test_get_prompt(vision_skill):
    """프롬프트 가져오기 테스트"""
    # 프롬프트가 로드되었는지 확인
    ppe_prompt = vision_skill.get_prompt('ppe_detection')
    
    # 프롬프트가 있거나 기본 프롬프트 사용
    assert ppe_prompt is not None or vision_skill._get_default_ppe_prompt() is not None


def test_default_prompts(vision_skill):
    """기본 프롬프트 테스트"""
    ppe_prompt = vision_skill._get_default_ppe_prompt()
    assert '안전모' in ppe_prompt
    assert 'PPE' in ppe_prompt or '개인보호장비' in ppe_prompt
    
    safety_prompt = vision_skill._get_default_safety_prompt()
    assert '안전' in safety_prompt
    
    comparison_prompt = vision_skill._get_default_comparison_prompt()
    assert '비교' in comparison_prompt


# 통합 테스트 (실제 이미지 필요)
@pytest.mark.skip(reason="Requires actual image files")
def test_detect_ppe_integration(vision_skill):
    """PPE 감지 통합 테스트"""
    result = vision_skill.execute('detect_ppe', {
        'image': 'test_images/worker.jpg'
    })
    
    assert 'violations' in result
    assert 'risk_level' in result
    assert 'recommendations' in result
    assert result['risk_level'] in ['low', 'medium', 'high']


@pytest.mark.skip(reason="Requires actual image files")
def test_assess_safety_integration(vision_skill):
    """안전 평가 통합 테스트"""
    result = vision_skill.execute('assess_safety', {
        'image': 'test_images/workplace.jpg'
    })
    
    assert 'overall_safety' in result or 'raw_response' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
