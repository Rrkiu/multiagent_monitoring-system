---
name: vision_analysis
description: 이미지 기반 안전 분석 및 PPE 감지
version: 1.0.0
author: Safety Team
dependencies:
  - PIL
  - google-generativeai
  - langchain-google-genai
tags:
  - vision
  - safety
  - ppe
  - analysis
  - multimodal
---

# Vision Analysis Skill

이미지 기반 안전 분석을 수행하는 Skill입니다.

## 📋 기능

### 1. PPE(개인보호장비) 위반 감지
- 안전모 착용 여부
- 안전 조끼 착용 여부
- 안전화 착용 여부
- 보호 장갑 착용 여부

### 2. 작업장 안전 상태 평가
- 전반적인 안전 상태 평가
- 위험 요소 식별
- 위험도 등급 산정
- 개선 권고사항 제시

### 3. 다중 이미지 비교 분석
- 여러 이미지 동시 분석
- 시간대별 비교
- 카메라별 비교

### 4. 개선 전후 비교
- Before/After 비교
- 개선 효과 측정
- 변화 분석

## 🚀 사용법

### 기본 사용

```python
from skills.skill_manager import SkillManager

# Skill Manager 초기화
manager = SkillManager()

# Vision Analysis Skill 가져오기
vision_skill = manager.get_skill('vision_analysis')

# PPE 감지
result = vision_skill.execute('detect_ppe', {
    'image': 'path/to/image.jpg'
})

print(result['violations'])
print(result['risk_level'])
```

### 고급 사용

```python
# 안전 평가
assessment = vision_skill.execute('assess_safety', {
    'image': 'path/to/workplace.jpg',
    'context': '건설 현장'
})

# 이미지 비교
comparison = vision_skill.execute('compare_images', {
    'before_image': 'before.jpg',
    'after_image': 'after.jpg'
})

# 다중 이미지 분석
multi_result = vision_skill.execute('analyze_multiple', {
    'images': ['img1.jpg', 'img2.jpg', 'img3.jpg'],
    'query': '모든 이미지에서 안전모 착용 여부를 확인해주세요'
})
```

## 📊 API

### execute(task, context)

**Parameters:**
- `task` (str): 수행할 작업
  - `detect_ppe`: PPE 감지
  - `assess_safety`: 안전 평가
  - `compare_images`: 이미지 비교
  - `analyze_multiple`: 다중 이미지 분석
  - `analyze_with_context`: 컨텍스트 기반 분석
- `context` (dict): 작업 컨텍스트
  - `image`: 이미지 경로 (필수)
  - `query`: 사용자 질문 (선택)
  - `camera_id`: 카메라 ID (선택)
  - `before_image`: 이전 이미지 (compare_images용)
  - `after_image`: 이후 이미지 (compare_images용)
  - `images`: 이미지 리스트 (analyze_multiple용)

**Returns:**
- dict: 작업 결과
  - `violations`: 위반 사항 리스트
  - `risk_level`: 위험도 (low, medium, high)
  - `recommendations`: 권고사항
  - `confidence`: 신뢰도 (0-1)

## 📝 예시

### PPE 감지 예시

```python
result = vision_skill.execute('detect_ppe', {
    'image': 'worker_01.jpg'
})

# 결과
{
    'violations': [
        {
            'type': 'helmet_missing',
            'severity': 'high',
            'confidence': 0.95,
            'location': {'x': 120, 'y': 80}
        }
    ],
    'risk_level': 'high',
    'recommendations': [
        '안전모 착용 필수',
        '작업 중단 권고'
    ]
}
```

### 안전 평가 예시

```python
result = vision_skill.execute('assess_safety', {
    'image': 'workplace.jpg',
    'context': '건설 현장'
})

# 결과
{
    'overall_safety': 'medium',
    'hazards': [
        {
            'type': 'unguarded_edge',
            'severity': 'high',
            'description': '낙하 위험이 있는 개방된 가장자리'
        }
    ],
    'ppe_compliance': 0.75,
    'recommendations': [
        '가장자리 안전 난간 설치',
        'PPE 착용률 개선 필요'
    ]
}
```

## ⚙️ 설정

`config.yaml` 파일에서 설정을 변경할 수 있습니다:

```yaml
vision_model: "gemini-2.0-flash-exp"
max_image_size: 1024
confidence_threshold: 0.7
ppe_types:
  - helmet
  - safety_vest
  - safety_shoes
  - gloves
```

## 🧪 테스트

```bash
# 단위 테스트
pytest skills/vision_analysis/tests/test_vision_analysis.py

# 통합 테스트
pytest skills/vision_analysis/tests/test_integration.py
```

## 📚 더 알아보기

- [예시 코드](examples/)
- [테스트 코드](tests/)
- [프롬프트 템플릿](prompts/)

## 🔧 문제 해결

### 이미지 로드 실패
- 이미지 경로가 올바른지 확인
- 지원되는 포맷인지 확인 (JPG, PNG, WebP)
- 파일 크기가 10MB 이하인지 확인

### 낮은 정확도
- 이미지 해상도 확인
- 조명 상태 확인
- 프롬프트 튜닝 고려

## 📄 라이선스

MIT License

## 👥 기여

버그 리포트 및 기능 제안을 환영합니다!
