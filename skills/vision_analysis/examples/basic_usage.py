"""
Vision Analysis Skill 사용 예시
"""

from skills.skill_manager import SkillManager


def example_1_ppe_detection():
    """예시 1: PPE 감지"""
    print("=" * 60)
    print("예시 1: PPE 감지")
    print("=" * 60)
    
    # Skill Manager 초기화
    manager = SkillManager()
    
    # Vision Analysis Skill 가져오기
    vision_skill = manager.get_skill('vision_analysis')
    
    # PPE 감지 실행
    result = vision_skill.execute('detect_ppe', {
        'image': 'uploaded_images/worker_01.jpg',
        'camera_id': 'cam_01'
    })
    
    print(f"\n위반 사항: {result['violations']}")
    print(f"위험도: {result['risk_level']}")
    print(f"권고사항: {result['recommendations']}")
    print()


def example_2_safety_assessment():
    """예시 2: 작업장 안전 평가"""
    print("=" * 60)
    print("예시 2: 작업장 안전 평가")
    print("=" * 60)
    
    manager = SkillManager()
    vision_skill = manager.get_skill('vision_analysis')
    
    # 안전 평가 실행
    result = vision_skill.execute('assess_safety', {
        'image': 'uploaded_images/workplace.jpg',
        'context': '건설 현장 A동'
    })
    
    print(f"\n전반적인 안전도: {result.get('overall_safety')}")
    print(f"발견된 위험 요소: {result.get('hazards')}")
    print(f"권고사항: {result.get('recommendations')}")
    print()


def example_3_image_comparison():
    """예시 3: 개선 전후 비교"""
    print("=" * 60)
    print("예시 3: 개선 전후 비교")
    print("=" * 60)
    
    manager = SkillManager()
    vision_skill = manager.get_skill('vision_analysis')
    
    # 이미지 비교 실행
    result = vision_skill.execute('compare_images', {
        'before_image': 'uploaded_images/before.jpg',
        'after_image': 'uploaded_images/after.jpg'
    })
    
    print(f"\n변화 사항: {result.get('changes')}")
    print(f"개선 여부: {result.get('improvement')}")
    print(f"요약: {result.get('summary')}")
    print()


def example_4_multiple_images():
    """예시 4: 다중 이미지 분석"""
    print("=" * 60)
    print("예시 4: 다중 이미지 분석")
    print("=" * 60)
    
    manager = SkillManager()
    vision_skill = manager.get_skill('vision_analysis')
    
    # 다중 이미지 분석 실행
    result = vision_skill.execute('analyze_multiple', {
        'images': [
            'uploaded_images/worker_01.jpg',
            'uploaded_images/worker_02.jpg',
            'uploaded_images/worker_03.jpg'
        ],
        'query': '모든 이미지에서 안전모 착용 여부를 확인해주세요'
    })
    
    print(f"\n분석된 이미지 수: {result['total_images']}")
    print(f"요약: {result['summary']}")
    
    for idx, item in enumerate(result['results']):
        print(f"\n이미지 {idx + 1}:")
        print(f"  - 위험도: {item['result']['risk_level']}")
        print(f"  - 위반 사항 수: {len(item['result']['violations'])}")
    print()


def example_5_skill_manager():
    """예시 5: Skill Manager 사용"""
    print("=" * 60)
    print("예시 5: Skill Manager 사용")
    print("=" * 60)
    
    manager = SkillManager()
    
    # 사용 가능한 Skills 목록
    print(f"\n사용 가능한 Skills: {manager.list_skills()}")
    
    # Vision Analysis Skill 정보
    vision_skill = manager.get_skill('vision_analysis')
    print(f"\nSkill 이름: {vision_skill.metadata.name}")
    print(f"버전: {vision_skill.metadata.version}")
    print(f"설명: {vision_skill.metadata.description}")
    print(f"기능: {vision_skill.get_capabilities()}")
    
    # Skill Manager를 통한 직접 실행
    result = manager.execute_skill(
        skill_name='vision_analysis',
        task='detect_ppe',
        context={'image': 'uploaded_images/worker_01.jpg'}
    )
    
    print(f"\n실행 성공: {result['success']}")
    print(f"사용된 Skill: {result['skill']}")
    print(f"수행된 작업: {result['task']}")
    print()


if __name__ == "__main__":
    print("\n🚀 Vision Analysis Skill 예시 코드\n")
    
    # 주의: 실제 이미지 파일이 필요합니다
    print("⚠️  주의: 이 예시를 실행하려면 uploaded_images/ 디렉토리에 이미지 파일이 필요합니다.\n")
    
    try:
        example_1_ppe_detection()
        example_2_safety_assessment()
        example_3_image_comparison()
        example_4_multiple_images()
        example_5_skill_manager()
        
        print("✅ 모든 예시 실행 완료!")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        print("\n이미지 파일을 준비한 후 다시 시도해주세요.")
