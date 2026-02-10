"""
Knowledge Management Skill 사용 예시
"""

from skills.skill_manager import SkillManager


def example_1_search_knowledge():
    """예시 1: 지식 베이스 검색"""
    print("=" * 60)
    print("예시 1: 지식 베이스 검색")
    print("=" * 60)
    
    manager = SkillManager()
    km_skill = manager.get_skill('knowledge_management')
    
    # 지식 검색
    result = km_skill.execute('search_knowledge', {
        'query': '안전모를 착용하지 않았을 때 어떻게 해야 하나요?',
        'k': 3
    })
    
    print(f"\n검색 쿼리: {result.get('query')}")
    print(f"검색 결과 수: {result.get('total_results')}")
    
    for idx, doc in enumerate(result.get('results', []), 1):
        print(f"\n[결과 {idx}]")
        print(f"  이벤트 타입: {doc['event_type']}")
        print(f"  출처: {doc['source_file']}")
        print(f"  내용 미리보기: {doc['content'][:150]}...")
    print()


def example_2_get_action_guide():
    """예시 2: 조치 가이드 조회"""
    print("=" * 60)
    print("예시 2: 조치 가이드 조회")
    print("=" * 60)
    
    manager = SkillManager()
    km_skill = manager.get_skill('knowledge_management')
    
    # 조치 가이드 조회
    event_types = ['NO_HELMET', 'FALL_DETECTED', 'FIRE_HAZARD']
    
    for event_type in event_types:
        result = km_skill.execute('get_action_guide', {
            'event_type': event_type
        })
        
        print(f"\n이벤트 타입: {result.get('event_type')}")
        print(f"조치 가이드:")
        print(result.get('guide', '가이드를 찾을 수 없습니다.')[:300] + "...")
        print("-" * 60)
    print()


def example_3_search_regulations():
    """예시 3: 안전 규정 검색"""
    print("=" * 60)
    print("예시 3: 안전 규정 검색")
    print("=" * 60)
    
    manager = SkillManager()
    km_skill = manager.get_skill('knowledge_management')
    
    # 안전 규정 검색
    result = km_skill.execute('search_regulations', {
        'query': '안전모 착용 관련 법규',
        'k': 2
    })
    
    print(f"\n검색 쿼리: {result.get('query')}")
    print(f"검색 결과 수: {result.get('total_results')}")
    
    for idx, reg in enumerate(result.get('regulations', []), 1):
        print(f"\n[규정 {idx}]")
        print(f"  이벤트 타입: {reg['event_type']}")
        print(f"  내용: {reg['content'][:200]}...")
    print()


def example_4_search_by_event_type():
    """예시 4: 이벤트 타입별 검색"""
    print("=" * 60)
    print("예시 4: 이벤트 타입별 검색")
    print("=" * 60)
    
    manager = SkillManager()
    km_skill = manager.get_skill('knowledge_management')
    
    # 이벤트 타입별 검색
    result = km_skill.execute('search_by_event_type', {
        'event_type': 'NO_HELMET',
        'k': 2
    })
    
    print(f"\n이벤트 타입: {result.get('event_type')}")
    print(f"검색 결과 수: {result.get('total_results')}")
    
    for idx, doc in enumerate(result.get('results', []), 1):
        print(f"\n[결과 {idx}]")
        print(f"  내용: {doc['content'][:200]}...")
    print()


def example_5_answer_question():
    """예시 5: 질문 답변 (RAG + LLM)"""
    print("=" * 60)
    print("예시 5: 질문 답변 (RAG + LLM)")
    print("=" * 60)
    
    manager = SkillManager()
    km_skill = manager.get_skill('knowledge_management')
    
    # 질문에 대한 답변 생성
    questions = [
        "작업자가 안전모를 착용하지 않았을 때 어떻게 대응해야 하나요?",
        "낙상 사고가 발생했을 때 즉시 취해야 할 조치는 무엇인가요?"
    ]
    
    for question in questions:
        result = km_skill.execute('answer_question', {
            'question': question,
            'k': 3
        })
        
        print(f"\n질문: {result.get('question')}")
        print(f"\n답변:")
        print(result.get('answer'))
        print(f"\n사용된 출처: {result.get('context_used')}개 문서")
        print(f"출처 정보:")
        for source in result.get('sources', []):
            print(f"  - {source['event_type']} ({source['source_file']})")
        print("-" * 60)
    print()


def example_6_skill_manager():
    """예시 6: Skill Manager를 통한 실행"""
    print("=" * 60)
    print("예시 6: Skill Manager를 통한 실행")
    print("=" * 60)
    
    manager = SkillManager()
    
    # 사용 가능한 Skills 확인
    print(f"\n사용 가능한 Skills: {manager.list_skills()}")
    
    # Knowledge Management Skill 정보
    km_skill = manager.get_skill('knowledge_management')
    print(f"\nSkill 이름: {km_skill.metadata.name}")
    print(f"버전: {km_skill.metadata.version}")
    print(f"설명: {km_skill.metadata.description}")
    print(f"기능: {km_skill.get_capabilities()}")
    
    # Skill Manager를 통한 직접 실행
    result = manager.execute_skill(
        skill_name='knowledge_management',
        task='search_knowledge',
        context={
            'query': '화재 위험 발견 시 대응 방법',
            'k': 2
        }
    )
    
    print(f"\n실행 성공: {result.get('success', True)}")
    if 'result' in result:
        print(f"검색 결과 수: {result['result'].get('total_results')}")
    print()


def example_7_rebuild_vectorstore():
    """예시 7: 벡터 스토어 재구축"""
    print("=" * 60)
    print("예시 7: 벡터 스토어 재구축")
    print("=" * 60)
    
    manager = SkillManager()
    km_skill = manager.get_skill('knowledge_management')
    
    # 벡터 스토어 재구축
    print("\n벡터 스토어 재구축 중...")
    result = km_skill.execute('rebuild_vectorstore', {})
    
    if result.get('success'):
        print(f"✅ {result.get('message')}")
    else:
        print(f"❌ {result.get('error')}")
    print()


if __name__ == "__main__":
    print("\n🚀 Knowledge Management Skill 예시 코드\n")
    
    try:
        example_1_search_knowledge()
        example_2_get_action_guide()
        example_3_search_regulations()
        example_4_search_by_event_type()
        # example_5_answer_question()  # LLM 호출 필요
        example_6_skill_manager()
        # example_7_rebuild_vectorstore()  # 시간이 오래 걸림
        
        print("✅ 모든 예시 실행 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()
