# 멀티모달 에이전트 빠른 시작 가이드

## 🚀 빠른 시작

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

새로 추가된 패키지:
- `Pillow==10.2.0` - 이미지 처리

### 2. 테스트 실행

```bash
# 멀티모달 에이전트 단독 테스트
python test_multimodal_agent.py
```

### 3. API 사용 예시

#### Python으로 API 호출

```python
import requests
import base64

# 1. 로그인
login_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = login_response.json()["access_token"]

# 2. 이미지를 Base64로 인코딩
with open("your_image.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

# 3. 멀티모달 쿼리 전송
response = requests.post(
    "http://localhost:8000/api/multimodal-query",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "query": "이 이미지에서 안전 위반 사항을 찾아주세요",
        "images": [f"data:image/jpeg;base64,{image_base64}"]
    }
)

print(response.json()["response"])
```

#### cURL로 API 호출

```bash
# 1. 로그인하여 토큰 획득
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# 2. 이미지를 Base64로 인코딩
IMAGE_BASE64=$(base64 -w 0 your_image.jpg)

# 3. 멀티모달 쿼리
curl -X POST "http://localhost:8000/api/multimodal-query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"query\": \"이 이미지의 안전 상태를 평가해주세요\",
    \"images\": [\"data:image/jpeg;base64,$IMAGE_BASE64\"]
  }"
```

## 📋 주요 기능

### 1. 안전 위반 사항 감지
```python
from agents.multimodal_agent import MultimodalAgent

agent = MultimodalAgent()
result = agent.analyze_image("workplace.jpg", "안전 위반 사항을 찾아주세요")
```

### 2. PPE 착용 확인
```python
result = agent.detect_ppe_violations("workplace.jpg")
```

### 3. 작업장 안전 평가
```python
result = agent.assess_workplace_safety("workplace.jpg")
```

### 4. 개선 전후 비교
```python
result = agent.compare_before_after("before.jpg", "after.jpg")
```

### 5. 다중 이미지 분석
```python
result = agent.analyze_multiple_images(
    ["image1.jpg", "image2.jpg", "image3.jpg"],
    "세 작업장의 안전 상태를 비교해주세요"
)
```

## 🎯 사용 예시

### 예시 1: CCTV 스냅샷 분석
```
질문: "이 CCTV 이미지에서 안전모를 착용하지 않은 작업자를 찾아주세요"

응답:
{
  "detected_violations": [
    {
      "category": "PPE 미착용",
      "description": "작업자 1명이 안전모를 착용하지 않음",
      "severity": "HIGH",
      "location": "이미지 중앙 왼쪽"
    }
  ],
  "worker_count": 3,
  "overall_risk_level": "HIGH",
  "recommendations": [
    "즉시 작업 중단 및 안전모 착용 지시",
    "안전 교육 재실시"
  ],
  "summary": "3명의 작업자 중 1명이 안전모 미착용 상태로 즉각 조치 필요"
}
```

### 예시 2: 작업장 안전 점검
```
질문: "이 작업장의 전반적인 안전 상태를 평가해주세요"

응답:
- 작업 환경 정리정돈: 양호
- 안전 표지판: 부족 (개선 필요)
- 비상구 표시: 명확
- 소화기 배치: 적절
- 위험 구역 차단: 미흡 (안전 펜스 필요)
- 전반적 위험도: MEDIUM

권장 사항:
1. 위험 구역에 안전 펜스 설치
2. 안전 표지판 추가 배치
3. 정기적인 안전 점검 실시
```

## 🔧 설정

### config/settings.py
```python
# 멀티모달 설정
vision_model: str = "gemini-2.5-flash-lite"
max_image_size_mb: int = 10
supported_image_formats: list = ["jpg", "jpeg", "png", "webp", "gif"]
image_upload_dir: str = "./data/uploaded_images"
```

### 지원 이미지 포맷
- JPG / JPEG
- PNG
- WEBP
- GIF

### 이미지 크기 제한
- 최대 파일 크기: 10MB
- 자동 리사이징: 1024x1024 (비율 유지)

## 📚 상세 문서

전체 구현 문서는 다음을 참조하세요:
- [멀티모달 에이전트 구현 문서](./documents/MULTIMODAL_AGENT_IMPLEMENTATION.md)

## 🐛 문제 해결

### 이미지 로드 실패
```python
# 이미지 형식 확인
from tools.vision_tools import validate_image_format, validate_image_size

if not validate_image_format("image.jpg"):
    print("지원하지 않는 이미지 포맷입니다")

if not validate_image_size("image.jpg"):
    print("이미지 크기가 너무 큽니다 (최대 10MB)")
```

### API 호출 실패
- JWT 토큰이 유효한지 확인
- 이미지가 올바르게 Base64 인코딩되었는지 확인
- 네트워크 연결 상태 확인

### 분석 결과가 부정확한 경우
- 이미지 해상도를 높여보세요
- 더 명확한 질문을 작성하세요
- 여러 각도의 이미지를 제공하세요

## 📞 지원

문제가 발생하면 다음을 확인하세요:
1. 로그 파일 확인
2. API 응답 메시지 확인
3. 테스트 스크립트 실행 (`python test_multimodal_agent.py`)

---

**업데이트**: 2025-12-12  
**버전**: 1.0.0
