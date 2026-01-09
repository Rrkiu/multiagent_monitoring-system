# Safety Monitoring Multi-Agent System

안전 모니터링을 위한 멀티 에이전트 시스템입니다. Google Gemini API를 활용하여 다양한 안전 관련 작업을 수행합니다.

## 주요 기능

- 🤖 **멀티 에이전트 시스템**: 여러 전문화된 에이전트가 협력하여 작업 수행
- 🔍 **검색 에이전트**: 웹 검색 및 정보 수집
- 🖼️ **멀티모달 에이전트**: 이미지 분석 및 비전 작업
- 📊 **분석 에이전트**: 데이터 분석 및 리포트 생성
- 🔐 **보안 에이전트**: 보안 관련 검증 및 모니터링
- 👤 **JWT 인증**: 안전한 사용자 인증 및 권한 관리

## 기술 스택

- **Backend**: FastAPI, Python 3.10+
- **AI/ML**: Google Gemini API, LangChain
- **Database**: SQLite, ChromaDB (Vector Store)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: JWT (JSON Web Tokens)

## 설치 방법

### 1. 저장소 클론

```bash
git clone <repository-url>
cd safety_multiagent
```

### 2. 가상 환경 생성 및 활성화

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정

`.env.example` 파일을 `.env`로 복사하고 필요한 값을 설정합니다:

```bash
cp .env.example .env
```

`.env` 파일을 열어 다음 값들을 설정하세요:

- `GOOGLE_API_KEY`: Google Gemini API 키
- `SECRET_KEY`: JWT 토큰 생성을 위한 비밀 키 (32자 이상 권장)

### 5. 데이터 디렉토리 생성

```bash
mkdir -p data/vector_store data/knowledge_base data/uploaded_images
```

## 실행 방법

### 개발 서버 실행

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

서버가 실행되면 다음 주소로 접속할 수 있습니다:

- **Frontend**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 프로젝트 구조

```
safety_multiagent/
├── agents/              # 에이전트 모듈
│   ├── multimodal_agent.py
│   ├── search_agent.py
│   ├── analysis_agent.py
│   ├── security_agent.py
│   └── supervisor_agent.py
├── auth/               # 인증 관련 모듈
│   ├── auth_handler.py
│   ├── models.py
│   └── routes.py
├── config/             # 설정 파일
│   └── settings.py
├── data/               # 데이터 저장소
│   ├── vector_store/   # 벡터 DB
│   ├── knowledge_base/ # 지식 베이스
│   └── uploaded_images/
├── frontend/           # 프론트엔드 파일
│   ├── index.html
│   └── auth.js
├── tools/              # 도구 모듈
├── utils/              # 유틸리티 함수
├── app.py              # 메인 애플리케이션
└── requirements.txt    # 의존성 목록
```

## API 사용 예시

### 1. 사용자 등록

```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "email": "user@example.com", "password": "password123"}'
```

### 2. 로그인

```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password123"}'
```

### 3. 멀티모달 분석

```bash
curl -X POST "http://localhost:8000/multimodal/analyze" \
  -H "Authorization: Bearer <your-token>" \
  -F "file=@image.jpg" \
  -F "query=이 이미지에서 안전 문제를 찾아주세요"
```

## 환경 변수

| 변수명 | 설명 | 기본값 |
|--------|------|--------|
| `GOOGLE_API_KEY` | Google Gemini API 키 | 필수 |
| `SECRET_KEY` | JWT 비밀 키 | 필수 (프로덕션에서 변경) |
| `LLM_MODEL` | 사용할 LLM 모델 | gemma-3-27b-it |
| `VISION_MODEL` | 비전 모델 | gemini-2.5-flash-image |
| `DEBUG` | 디버그 모드 | True |

## 보안 주의사항

⚠️ **중요**: 프로덕션 환경에서는 반드시 다음 사항을 확인하세요:

1. `.env` 파일의 `SECRET_KEY`를 강력한 랜덤 값으로 변경
2. `DEBUG=False` 설정
3. HTTPS 사용
4. 적절한 CORS 설정
5. 데이터베이스 백업 설정

## 테스트

```bash
# 멀티모달 에이전트 테스트
python test_multimodal_agent.py

# 검색 에이전트 테스트
python test_search_agent.py

# 보안 테스트
python test_security.py
```

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!

## 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.
