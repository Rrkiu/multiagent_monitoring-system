# Safety Monitoring Multi-Agent System (LangGraph + Skills Architecture)

> 🚀 **LangGraph 기반 차세대 아키텍처**  
> 이 프로젝트는 기존의 단순 Agent + Tools 구조를 넘어, **LangGraph 기반의 Supervisor 제어 타워**와 **독립적인 플러그인 형태의 Skills**로 고도화된 버전입니다.

작업장 안전 모니터링을 위한 지능형 멀티 에이전트 시스템입니다. Google Gemini API를 활용하여, 사용자의 질의를 분석하고 적절한 안전 점검, 데이터 분석, 지식 검색, 보고서 생성 작업을 자동화하여 수행합니다.

---

## 🎯 주요 아키텍처 특징

### 1. LangGraph 기반 Supervisor (M1/M2)
- **제어 역전(IoC)**: LLM이 스스로 판단하던 불확실한 제어 흐름을 LangGraph의 명시적 StateGraph 상태 머신으로 대체.
- **영속적 대화 메모리 (M2)**: `SqliteSaver`를 통해 사용자 세션별 대화 이력을 데이터베이스에 영속적으로 저장.
- **에러 복구 파이프라인 (M2)**: 스킬 실행 실패 시 Router로 피드백 루프를 형성하여 최대 3회까지 자동 재라우팅/재시도.
- **병렬 분기 처리 (M2)**: LangGraph `Send` API를 통해 멀티스텝 작업 요청 시 독립된 여러 스킬을 동시에 병렬 실행 후 결과를 합성.

### 2. Skills 플러그인 시스템
모든 기능이 독립적인 Skill 모듈로 분리되어 응집도가 높고 확장이 용이합니다.
- 🔍 **Vision Analysis Skill**: 이미지 기반 안전 위반(PPE 미착용, 낙상, 화재 등) 감지
- 📊 **Data Analytics Skill**: 이벤트 데이터 조회, 통계, 추세 및 위험도 분석
- 🧠 **Knowledge Management Skill**: RAG(ChromaDB) 기반 산업안전보건법 및 대응 가이드 검색
- 📝 **Report Generation Skill**: 복합적인 분석 결과를 바탕으로 안전 조치 보고서 자동 생성

### 3. 안전 우선 라우팅 및 보안 
- **3중 도메인 필터**: 안전과 무관한 질의(예: "오늘 날씨 어때?")를 LLM 호출 전에 선제적으로 차단 (`_is_safety_domain`).
- **Security Node**: 시스템 프롬프트 변조 및 악의적인 인젝션 시도를 그래프의 최우선 진입점에서 검열 및 차단.

---

## 🛠️ 기술 스택

- **Backend**: Python 3.10+, FastAPI
- **Workflow / AI**: LangGraph, LangChain, Google Gemini-3-27b-it
- **Database / Vector Store**: SQLite3, ChromaDB, Sentence-Transformers (MiniLM)
- **Frontend**: Vanilla HTML / JS / CSS
- **Authentication**: JWT (JSON Web Tokens)
- **Testing**: Pytest, Pytest-Asyncio

---

## 📦 폴더 구조

```text
safety_multiagent/
├── agents/                 # LangGraph 정의 및 라우팅 로직
│   ├── supervisor_langgraph.py  # 메인 제어 타워 (StateGraph)
│   ├── security_agent.py   # 인젝션 방어
│   └── state.py            # AgentState 타입 정의
├── skills/                 # 핵심 기능 플러그인 (Skills)
│   ├── base_skill.py       # 추상 클래스
│   ├── skill_manager.py    # 동적 로딩 및 통합 실행 관리자
│   ├── data_analytics/
│   ├── knowledge_management/
│   ├── report_generation/
│   └── vision_analysis/
├── auth/                   # JWT 인증 시스템 (경량)
├── config/                 # Pydantic 설정 관리
├── data/                   # 로컬 데이터 볼륨
│   ├── agent_memory.db     # LangGraph 체크포인트 영속성 저장소
│   ├── knowledge_base/     # RAG 마크다운 지식 문서들
│   └── vector_store/       # ChromaDB 로컬 파일
├── utils/                  # 세션 관리 (TTL) 및 RAG/포매팅 유틸 
├── tests/                  # Pytest 통합 테스트 스위트
│   ├── test_a_complex_scenarios.py # 복합 시나리오 검증
│   ├── test_b_api_endpoints.py     # API 레벨 검증
│   ├── test_c_graph_internals.py   # LangGraph 노드 및 라우팅 검증 
│   └── test_d_multi_turn.py        # 세션 격리 및 메모리 검증
├── documents/              # 아키텍처 마일스톤 및 구조 설계 문서 (M1/M2)
└── app.py                  # FastAPI 엔트리 포인트
```

---

## 🚀 설치 및 실행 방법

### 1. 환경 설정 및 의존성 설치

```bash
# 가상환경 생성 및 진입
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정
최상위 경로에 `.env` 파일을 생성하고 다음 값을 입력합니다.

```env
GOOGLE_API_KEY=your_gemini_api_key_here
SECRET_KEY=your_jwt_secret_key_here (32자 이상의 임의 문자열)
```

### 3. 애플리케이션 실행

```bash
python -m uvicorn app:app --host 0.0.0.0 --port 8000
```
- **웹 UI**: [http://localhost:8000](http://localhost:8000) 접속 후 기본 계정(`admin` / `admin123`)으로 로그인.
- **API Docs**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 🧪 테스트 실행

마일스톤 4(M4)에서 완성된 방대한 단위/통합 테스트 스위트를 실행하려면 루트에서 다음 명령어를 실행합니다.

```bash
# 전체 테스트 실행
pytest

# 특정 카테고리 테스트 실행
pytest tests/test_c_graph_internals.py -v
```

---

## 📡 주요 API 엔트리포인트

- `POST /api/query`: 텍스트 기반 안전 질의 요청. JSON으로 `{ "query": "..." }` 전달.
- `POST /api/multimodal-query`: 이미지와 텍스트를 함께 분석. Multipart FormData로 사진과 쿼리 전송.
- `GET /api/agents`: 시스템 내 로드된 스킬(Agent) 목록 및 능력 반환.

*(모든 `/api/*` 주소는 JWT 인증(`Bearer Token`)을 요구합니다.)*
