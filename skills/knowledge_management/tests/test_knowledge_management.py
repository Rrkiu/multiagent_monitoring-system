"""
Knowledge Management Skill 테스트
"""

import pytest
from skills.knowledge_management.skill import KnowledgeManagementSkill


@pytest.fixture
def km_skill():
    """Knowledge Management Skill 인스턴스"""
    return KnowledgeManagementSkill()


def test_skill_metadata(km_skill):
    """메타데이터 테스트"""
    assert km_skill.metadata.name == "knowledge_management"
    assert km_skill.metadata.version == "1.0.0"
    assert "knowledge" in km_skill.metadata.tags
    assert "rag" in km_skill.metadata.tags
    assert "search" in km_skill.metadata.tags


def test_skill_capabilities(km_skill):
    """기능 목록 테스트"""
    capabilities = km_skill.get_capabilities()
    
    assert "search_knowledge" in capabilities
    assert "get_action_guide" in capabilities
    assert "search_regulations" in capabilities
    assert "search_by_event_type" in capabilities
    assert "answer_question" in capabilities
    assert "rebuild_vectorstore" in capabilities


def test_validate_input_search_knowledge(km_skill):
    """입력 검증 테스트 - 지식 검색"""
    # 유효한 입력
    assert km_skill.validate_input('search_knowledge', {
        'query': '안전모 착용'
    }) == True
    
    # 무효한 입력 (query 없음)
    assert km_skill.validate_input('search_knowledge', {}) == False


def test_validate_input_action_guide(km_skill):
    """입력 검증 테스트 - 조치 가이드"""
    # 유효한 입력
    assert km_skill.validate_input('get_action_guide', {
        'event_type': 'NO_HELMET'
    }) == True
    
    # 무효한 입력 (event_type 없음)
    assert km_skill.validate_input('get_action_guide', {}) == False


def test_validate_input_regulations(km_skill):
    """입력 검증 테스트 - 안전 규정 검색"""
    # 유효한 입력
    assert km_skill.validate_input('search_regulations', {
        'query': '안전모 법규'
    }) == True
    
    # 무효한 입력
    assert km_skill.validate_input('search_regulations', {}) == False


def test_validate_input_event_type(km_skill):
    """입력 검증 테스트 - 이벤트 타입별 검색"""
    # 유효한 입력
    assert km_skill.validate_input('search_by_event_type', {
        'event_type': 'NO_HELMET'
    }) == True
    
    # 무효한 입력
    assert km_skill.validate_input('search_by_event_type', {}) == False


def test_validate_input_answer_question(km_skill):
    """입력 검증 테스트 - 질문 답변"""
    # 유효한 입력
    assert km_skill.validate_input('answer_question', {
        'question': '안전모를 착용하지 않으면 어떻게 하나요?'
    }) == True
    
    # 무효한 입력
    assert km_skill.validate_input('answer_question', {}) == False


def test_validate_input_rebuild(km_skill):
    """입력 검증 테스트 - 벡터 스토어 재구축"""
    # 파라미터 불필요
    assert km_skill.validate_input('rebuild_vectorstore', {}) == True
    assert km_skill.validate_input('rebuild_vectorstore', {'any': 'param'}) == True


def test_tools_initialization(km_skill):
    """도구 초기화 테스트"""
    assert 'llm' in km_skill.tools
    assert 'rag_system' in km_skill.tools
    assert 'knowledge_searcher' in km_skill.tools
    assert 'action_guide_retriever' in km_skill.tools
    assert 'regulation_searcher' in km_skill.tools


def test_default_answer_prompt(km_skill):
    """기본 답변 프롬프트 테스트"""
    prompt = km_skill._get_default_answer_prompt()
    
    assert '{context}' in prompt
    assert '{question}' in prompt
    assert '지침' in prompt or '가이드' in prompt


# 통합 테스트 (실제 RAG 시스템 필요)
@pytest.mark.skip(reason="Requires initialized RAG system")
def test_search_knowledge_integration(km_skill):
    """지식 검색 통합 테스트"""
    result = km_skill.execute('search_knowledge', {
        'query': '안전모 미착용',
        'k': 3
    })
    
    assert 'query' in result
    assert 'results' in result or 'message' in result


@pytest.mark.skip(reason="Requires initialized RAG system")
def test_get_action_guide_integration(km_skill):
    """조치 가이드 통합 테스트"""
    result = km_skill.execute('get_action_guide', {
        'event_type': 'NO_HELMET'
    })
    
    assert 'event_type' in result
    assert 'guide' in result


@pytest.mark.skip(reason="Requires initialized RAG system")
def test_search_by_event_type_integration(km_skill):
    """이벤트 타입별 검색 통합 테스트"""
    result = km_skill.execute('search_by_event_type', {
        'event_type': 'FALL_DETECTED',
        'k': 2
    })
    
    assert 'event_type' in result
    assert 'results' in result or 'message' in result


@pytest.mark.skip(reason="Requires initialized RAG system and LLM")
def test_answer_question_integration(km_skill):
    """질문 답변 통합 테스트"""
    result = km_skill.execute('answer_question', {
        'question': '낙상 사고 발생 시 어떻게 대응하나요?',
        'k': 3
    })
    
    assert 'question' in result
    assert 'answer' in result
    assert 'sources' in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
