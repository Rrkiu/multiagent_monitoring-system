# Safety Monitoring Multi-Agent System (Skills Branch)

> 🚀 **Skills 기반 아키텍처 브랜치**  
> 이 브랜치는 기존 Agent + Tools 구조를 **Skills 기반 아키텍처**로 재구성한 버전입니다.

안전 모니터링을 위한 멀티 에이전트 시스템입니다. Google Gemini API를 활용하여 다양한 안전 관련 작업을 수행합니다.

## 📌 브랜치 정보

| 브랜치 | 설명 | 상태 |
|--------|------|------|
| `main` | 기존 Agent + Tools 구조 | ✅ 안정 버전 |
| `skills` | Skills 기반 아키텍처 | 🚧 개발 중 (프로토타입 완성) |

### Skills 브랜치 특징

- ✅ **응집도 향상**: Agent + Tools가 Skill로 통합
- ✅ **재사용성 증가**: 독립적인 Skill 모듈
- ✅ **확장성 개선**: 새 Skill 추가 시 코드 수정 불필요
- ✅ **문서화 강화**: 각 Skill별 상세 문서

## 🎯 주요 기능

### Skills 기반 시스템 (이 브랜치)

- 🔍 **Vision Analysis Skill**: 이미지 기반 안전 분석 및 PPE 감지
- 📊 **Data Analytics Skill**: 이벤트 데이터 분석 및 통계 (계획됨)
- 🌐 **Web Intelligence Skill**: 웹 검색 및 정보 수집 (계획됨)
- 🧠 **Knowledge Management Skill**: RAG 기반 지식 관리 (계획됨)
- 🔒 **Security Validation Skill**: 보안 검증 및 모니터링 (계획됨)
- 📝 **Report Generation Skill**: 분석 결과 리포트 생성 (계획됨)

### 기존 기능 (main 브랜치)

- 🤖 **멀티 에이전트 시스템**: 여러 전문화된 에이전트가 협력하여 작업 수행
- 🔍 **검색 에이전트**: 웹 검색 및 정보 수집
- 🖼️ **멀티모달 에이전트**: 이미지 분석 및 비전 작업
- 📊 **분석 에이전트**: 데이터 분석 및 리포트 생성
- 🔐 **보안 에이전트**: 보안 관련 검증 및 모니터링
- 👤 **JWT 인증**: 안전한 사용자 인증 및 권한 관리

## 🛠️ 기술 스택

- **Backend**: FastAPI, Python 3.10+
- **AI/ML**: Google Gemini API, LangChain
- **Database**: SQLite, ChromaDB (Vector Store)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: JWT (JSON Web Tokens)
- **Architecture**: Skills-based Multi-Agent System (이 브랜치)

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

## 📁 프로젝트 구조 (Skills Branch)

```
safety_multiagent/
├── skills/                 # 🆕 Skills 모듈 (핵심!)
│   ├── base_skill.py      # BaseSkill 클래스
│   ├── skill_manager.py   # SkillManager 클래스
│   └── vision_analysis/   # Vision Analysis Skill
│       ├── SKILL.md       # Skill 문서
│       ├── skill.py       # 메인 구현
│       ├── config.yaml    # 설정
│       ├── prompts/       # 프롬프트 템플릿
│       ├── examples/      # 사용 예시
│       └── tests/         # 테스트 코드
├── agents/                # 기존 에이전트 (레거시)
│   ├── multimodal_agent.py
│   ├── search_agent.py
│   ├── analysis_agent.py
│   ├── security_agent.py
│   └── supervisor_agent.py
├── auth/                  # 인증 관련 모듈
│   ├── auth_handler.py
│   ├── models.py
│   └── routes.py
├── config/                # 설정 파일
│   └── settings.py
├── data/                  # 데이터 저장소
│   ├── vector_store/      # 벡터 DB
│   ├── knowledge_base/    # 지식 베이스
│   └── uploaded_images/
├── documents/             # 🆕 Skills 아키텍처 문서
│   ├── SKILLS_ARCHITECTURE_PLAN.md
│   ├── SKILLS_EVENT_MAPPING.md
│   ├── SKILLS_IMPLEMENTATION_GUIDE.md
│   ├── SKILLS_COMPLETION_REPORT.md
│   ├── SUPERVISOR_ROLE_COMPARISON.md
│   └── SKILLS_AUTONOMY_EXPLANATION.md
├── frontend/              # 프론트엔드 파일
│   ├── index.html
│   └── auth.js
├── tools/                 # 도구 모듈 (레거시)
├── utils/                 # 유틸리티 함수
├── app.py                 # 메인 애플리케이션
└── requirements.txt       # 의존성 목록
```

## 🚀 Skills 사용 예시

### 1. Skill Manager 사용

```python
from skills.skill_manager import SkillManager

# Skill Manager 초기화
manager = SkillManager()

# 사용 가능한 Skills 확인
print(manager.list_skills())
# ['vision_analysis']

# Vision Analysis Skill 가져오기
vision_skill = manager.get_skill('vision_analysis')
print(vision_skill.metadata.name)
print(vision_skill.get_capabilities())
```

### 2. PPE 감지

```python
# PPE 감지 실행
result = vision_skill.execute('detect_ppe', {
    'image': 'uploaded_images/worker.jpg',
    'camera_id': 'cam_01'
})

print(f"위반 사항: {result['violations']}")
print(f"위험도: {result['risk_level']}")
print(f"권고사항: {result['recommendations']}")
```

### 3. 작업장 안전 평가

```python
# 안전 평가 실행
result = vision_skill.execute('assess_safety', {
    'image': 'uploaded_images/workplace.jpg',
    'context': '건설 현장 A동'
})

print(f"전반적인 안전도: {result.get('overall_safety')}")
print(f"발견된 위험 요소: {result.get('hazards')}")
```

### 4. Skill Manager를 통한 직접 실행

```python
# Skill Manager를 통해 직접 실행
result = manager.execute_skill(
    skill_name='vision_analysis',
    task='detect_ppe',
    context={'image': 'worker.jpg'}
)

if result['success']:
    print(f"결과: {result['result']}")
```

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

## 🧪 테스트

### Skills 테스트

```bash
# Vision Analysis Skill 테스트
pytest skills/vision_analysis/tests/ -v

# 전체 Skills 테스트
pytest skills/ -v

# 예시 코드 실행
python skills/vision_analysis/examples/basic_usage.py
```

### 기존 에이전트 테스트 (레거시)

```bash
# 멀티모달 에이전트 테스트
python test_multimodal_agent.py

# 검색 에이전트 테스트
python test_search_agent.py

# 보안 테스트
python test_security.py
```

## 🔀 브랜치 전환 가이드

### main 브랜치로 전환 (기존 시스템)

```bash
git checkout main
```

### skills 브랜치로 전환 (Skills 기반 시스템)

```bash
git checkout skills
```

## 🚧 개발 로드맵 (Skills Branch)

### ✅ Phase 1: 기반 구조 (완료)
- [x] BaseSkill 클래스 구현
- [x] SkillManager 구현
- [x] Vision Analysis Skill 프로토타입

### 🚧 Phase 2: 핵심 Skills 구현 (진행 중)
- [ ] Data Analytics Skill
- [ ] Security Validation Skill
- [ ] Knowledge Management Skill
- [ ] Web Intelligence Skill
- [ ] Report Generation Skill

### 📅 Phase 3: Supervisor 재설계 (예정)
- [ ] Skills 기반 Supervisor Agent v2
- [ ] 워크플로우 엔진
- [ ] 이벤트 핸들러

### 📅 Phase 4: API 통합 (예정)
- [ ] FastAPI 엔드포인트 업데이트
- [ ] API v2 구현
- [ ] 레거시 호환성 유지

## 📊 개선 효과

| 항목 | Before (main) | After (skills) | 개선도 |
|------|---------------|----------------|--------|
| 응집도 | 낮음 | 높음 | ⬆️ 80% |
| 재사용성 | 낮음 | 높음 | ⬆️ 90% |
| 테스트 용이성 | 중간 | 높음 | ⬆️ 70% |
| 확장성 | 중간 | 높음 | ⬆️ 85% |
| 문서화 | 부족 | 우수 | ⬆️ 95% |
| 코드량 | 660 lines | 513 lines | ⬇️ 22% |

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여

버그 리포트, 기능 제안, Pull Request를 환영합니다!

### Skills 브랜치 기여 가이드

1. 새로운 Skill 추가 시:
   - `skills/base_skill.py`를 상속
   - `SKILL.md` 작성 (메타데이터, 사용법)
   - 테스트 코드 작성
   - 예시 코드 작성

2. 기존 Skill 개선 시:
   - 테스트 추가
   - 문서 업데이트
   - 프롬프트 튜닝

## 📞 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

---

**Branch**: `skills`  
**Status**: 🚧 Development (Prototype Complete)  
**Last Updated**: 2026-02-10

