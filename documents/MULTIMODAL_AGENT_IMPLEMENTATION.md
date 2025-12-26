# 멀티모달 에이전트 구현 문서

## 📋 개요

이미지와 텍스트를 동시에 처리할 수 있는 멀티모달 에이전트를 Safety Monitoring Multi-Agent System에 추가했습니다.

**구현 날짜**: 2025-12-12  
**모델**: Gemini 2.5 Flash Lite  
**주요 기능**: 이미지 기반 안전 점검, PPE 위반 감지, 작업장 안전 평가

---

## 🎯 주요 기능

### 1. 이미지 분석 기능
- ✅ 안전모(헬멧) 착용 여부 확인
- ✅ 안전복, 안전화, 보안경, 장갑 착용 상태 점검
- ✅ 작업자 자세 및 행동 분석
- ✅ 위험 구역 침입 감지
- ✅ 작업장 환경 안전 평가

### 2. 멀티모달 처리
- 단일 이미지 분석
- 다중 이미지 동시 분석 (비교 분석)
- 이미지 + 텍스트 컨텍스트 결합 처리
- 개선 전후 비교 분석

### 3. 입력 형식 지원
- Base64 인코딩된 이미지
- 파일 경로
- URL (HTTP/HTTPS)
- PIL Image 객체

---

## 📁 파일 구조

```
safety_multiagent/
├── agents/
│   ├── multimodal_agent.py          # 새로 추가 ⭐
│   └── supervisor_agent.py          # 업데이트 (라우팅 로직)
├── tools/
│   └── vision_tools.py               # 새로 추가 ⭐
├── config/
│   └── settings.py                   # 업데이트 (멀티모달 설정)
├── data/
│   └── uploaded_images/              # 새로 추가 (이미지 저장)
├── app.py                            # 업데이트 (새 엔드포인트)
├── requirements.txt                  # 업데이트 (Pillow 추가)
└── documents/
    └── MULTIMODAL_AGENT_IMPLEMENTATION.md  # 이 문서
```

---

## 🔧 구현 세부사항

### 1. MultimodalAgent 클래스

**위치**: `agents/multimodal_agent.py`

**주요 메서드**:
```python
# 단일 이미지 분석
analyze_image(image_source, query)

# 다중 이미지 분석
analyze_multiple_images(image_sources, query)

# 컨텍스트 고려 분석
analyze_with_context(image_source, query, context)

# PPE 위반 감지
detect_ppe_violations(image_source)

# 작업장 안전 평가
assess_workplace_safety(image_source)

# 개선 전후 비교
compare_before_after(before_image, after_image)
```

**특징**:
- Gemini 2.5 Flash Lite 모델 사용
- Temperature 0.3 (정확성 우선)
- 구조화된 JSON 응답 형식
- 위험도 레벨 평가 (LOW/MEDIUM/HIGH)

### 2. Vision Tools

**위치**: `tools/vision_tools.py`

**주요 함수**:
```python
# 이미지 로드
load_image_from_path(image_path)
load_image_from_url(image_url)
load_image_from_base64(base64_string)

# 이미지 변환
image_to_base64(image, format)
resize_image(image, max_size)

# 이미지 검증
validate_image_format(image_path)
validate_image_size(image_path)

# Gemini 전처리
prepare_image_for_gemini(image_source, resize, max_size)
process_multiple_images(image_sources, resize, max_size)

# 저장
save_uploaded_image(image, filename)
```

**지원 포맷**: JPG, JPEG, PNG, WEBP, GIF  
**최대 파일 크기**: 10MB  
**자동 리사이징**: 1024x1024 (비율 유지)

### 3. SupervisorAgent 통합

**업데이트 내용**:
1. MultimodalAgent import 및 초기화
2. 라우팅 프롬프트에 multimodal 에이전트 추가
3. `_execute_single_agent` 메서드에 `image_data` 파라미터 추가
4. 이미지 포함 쿼리 자동 감지 및 라우팅

**라우팅 로직**:
```
이미지 포함 쿼리 감지
    ↓
multimodal 에이전트 선택
    ↓
이미지 전처리 및 분석
    ↓
필요시 다른 에이전트와 연계 (멀티스텝)
```

### 4. API 엔드포인트

**새 엔드포인트**: `POST /api/multimodal-query`

**Request 모델**:
```python
class MultimodalQueryRequest(BaseModel):
    query: str                          # 사용자 질문
    images: Optional[List[str]] = None  # Base64 또는 파일 경로
    session_id: Optional[str] = None    # 세션 ID
```

**Response 모델**:
```python
class QueryResponse(BaseModel):
    response: str                       # 분석 결과
    session_id: Optional[str] = None    # 세션 ID
```

**인증**: JWT 토큰 필요 (기존 인증 시스템 활용)

**사용 예시**:
```bash
curl -X POST "http://localhost:8000/api/multimodal-query" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "이 이미지에서 안전 위반 사항을 찾아주세요",
    "images": ["data:image/jpeg;base64,/9j/4AAQ..."]
  }'
```

---

## 🔐 보안 고려사항

### 1. 이미지 검증
- ✅ 파일 크기 제한 (10MB)
- ✅ 허용된 형식만 업로드 (JPG, PNG, WEBP, GIF)
- ✅ 악성 파일 차단 (PIL을 통한 검증)

### 2. 인증 및 권한
- ✅ JWT 토큰 인증 필수
- ✅ 기존 사용자 권한 시스템 활용
- ✅ 세션 관리

### 3. 저장소 관리
- 업로드된 이미지는 `data/uploaded_images/` 디렉토리에 저장
- 권장: 주기적인 정리 작업 (예: 24시간 후 자동 삭제)
- 디스크 용량 모니터링 필요

---

## 📊 사용 시나리오

### 시나리오 1: 단일 이미지 안전 점검
```
입력: [이미지] + "이 작업장의 안전 상태를 평가해주세요"
↓
MultimodalAgent 분석
↓
출력: 
- 감지된 작업자 수: 3명
- 안전모 착용: 2/3 (1명 미착용)
- 위험도: MEDIUM
- 권장 사항: 미착용자에게 즉시 안전모 착용 지시
```

### 시나리오 2: PPE 위반 감지
```
입력: [이미지] + "PPE 착용 상태를 확인해주세요"
↓
detect_ppe_violations() 실행
↓
출력:
- 작업자 1: 안전모 ✓, 안전복 ✓, 안전화 ✓
- 작업자 2: 안전모 ✗, 안전복 ✓, 안전화 ✓
- 즉각 조치: 작업자 2에게 안전모 착용 필요
```

### 시나리오 3: 복합 분석 (멀티스텝)
```
입력: [이미지] + "이 구역의 위험 요소와 대응 방안을 제시해주세요"
↓
Step 1: MultimodalAgent (이미지 분석)
  → 위험 요소 식별: 안전 펜스 없음, 조명 부족
↓
Step 2: ReportAgent (대응 방안 생성)
  → 안전 펜스 설치 권장
  → 조명 개선 필요
  → 작업자 안전 교육 실시
↓
최종 응답: 종합 보고서
```

### 시나리오 4: 개선 전후 비교
```
입력: [이미지1, 이미지2] + "개선 전후를 비교해주세요"
↓
compare_before_after() 실행
↓
출력:
- 개선된 점: 안전 펜스 설치, 경고 표지판 추가
- 개선도: 75%
- 추가 권장: 비상구 표시 명확화
```

---

## 🧪 테스트 방법

### 1. 단위 테스트 (에이전트 직접 테스트)
```python
from agents.multimodal_agent import MultimodalAgent

agent = MultimodalAgent()

# 테스트 1: 단일 이미지 분석
result = agent.analyze_image("./test_image.jpg", "안전 상태 평가")
print(result)

# 테스트 2: PPE 위반 감지
result = agent.detect_ppe_violations("./test_image.jpg")
print(result)

# 테스트 3: 다중 이미지 분석
result = agent.analyze_multiple_images(
    ["./image1.jpg", "./image2.jpg"],
    "두 작업장을 비교 분석해주세요"
)
print(result)
```

### 2. API 테스트 (curl)
```bash
# 로그인하여 토큰 획득
TOKEN=$(curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' \
  | jq -r '.access_token')

# 멀티모달 쿼리 테스트
curl -X POST "http://localhost:8000/api/multimodal-query" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "이 이미지의 안전 상태를 평가해주세요",
    "images": ["data:image/jpeg;base64,BASE64_STRING_HERE"]
  }'
```

### 3. 통합 테스트 (Python)
```python
import requests
import base64

# 로그인
login_response = requests.post(
    "http://localhost:8000/auth/login",
    json={"username": "admin", "password": "admin123"}
)
token = login_response.json()["access_token"]

# 이미지를 Base64로 인코딩
with open("test_image.jpg", "rb") as f:
    image_base64 = base64.b64encode(f.read()).decode()

# 멀티모달 쿼리
response = requests.post(
    "http://localhost:8000/api/multimodal-query",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "query": "안전 위반 사항을 찾아주세요",
        "images": [f"data:image/jpeg;base64,{image_base64}"]
    }
)

print(response.json())
```

---

## 📈 성능 최적화

### 1. 이미지 전처리
- 자동 리사이징 (1024x1024)
- RGB 변환 (RGBA, Grayscale 등 통일)
- JPEG 압축 (Base64 전송 시)

### 2. 캐싱 전략 (향후 개선)
- 동일 이미지 재분석 방지
- 분석 결과 캐싱 (Redis 등)
- 이미지 해시 기반 중복 제거

### 3. 비동기 처리 (향후 개선)
- 대용량 이미지 비동기 업로드
- 백그라운드 분석 작업
- 진행 상태 실시간 업데이트

---

## 🔄 향후 개선 사항

### 1. 프론트엔드 통합
- [ ] 이미지 업로드 UI 구현
- [ ] 드래그 앤 드롭 지원
- [ ] 이미지 미리보기
- [ ] 분석 결과 시각화 (바운딩 박스 등)

### 2. 고급 기능
- [ ] 실시간 CCTV 스트림 분석
- [ ] 객체 감지 및 추적
- [ ] 히트맵 생성 (위험 구역 시각화)
- [ ] 시계열 분석 (동일 구역의 시간별 변화)

### 3. 모델 개선
- [ ] Fine-tuning (산업 안전 특화)
- [ ] 커스텀 객체 감지 모델 통합
- [ ] 앙상블 모델 (여러 모델 결과 종합)

### 4. 데이터 관리
- [ ] 이미지 자동 정리 스케줄러
- [ ] 분석 이력 저장 및 조회
- [ ] 이미지 메타데이터 관리
- [ ] 클라우드 스토리지 연동 (S3 등)

---

## 🐛 알려진 제한사항

1. **이미지 크기 제한**: 10MB (설정 변경 가능)
2. **동시 처리**: 현재 동기 처리 (비동기 개선 필요)
3. **모델 제약**: Gemini API 속도 제한 적용
4. **언어**: 한국어 중심 (다국어 지원 가능)

---

## 📚 참고 자료

- [Gemini API 문서](https://ai.google.dev/docs)
- [LangChain Google GenAI](https://python.langchain.com/docs/integrations/chat/google_generative_ai)
- [Pillow 문서](https://pillow.readthedocs.io/)

---

## ✅ 체크리스트

### 구현 완료
- [x] MultimodalAgent 클래스 구현
- [x] Vision Tools 유틸리티 구현
- [x] SupervisorAgent 통합
- [x] API 엔드포인트 추가
- [x] 설정 파일 업데이트
- [x] 의존성 추가 (Pillow)
- [x] 에이전트 목록 업데이트
- [x] 예시 쿼리 추가
- [x] 문서 작성

### 테스트 필요
- [ ] 단위 테스트 실행
- [ ] API 엔드포인트 테스트
- [ ] 다양한 이미지 포맷 테스트
- [ ] 에러 핸들링 테스트
- [ ] 성능 테스트

### 배포 전 확인
- [ ] 프로덕션 환경 설정 검토
- [ ] 보안 설정 강화
- [ ] 로깅 및 모니터링 설정
- [ ] 백업 전략 수립

---

## 📞 문의 및 지원

구현 관련 문의사항이나 버그 리포트는 프로젝트 관리자에게 연락하세요.

**구현 완료일**: 2025-12-12  
**버전**: 1.0.0  
**상태**: ✅ 구현 완료, 테스트 대기
