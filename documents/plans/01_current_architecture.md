# 현재 시스템 아키텍처 상세 문서
## LangChain 기반 Safety Monitoring Multi-Agent System

> 작성일: 2026-03-03  
> 목적: LLM 에이전트 학습용 — 현재 구동 방식 및 주요 항목 이해  
> 대상: AI Engineer 3년차 기준

---

## 목차

1. [시스템 개요](#1-시스템-개요)
2. [전체 아키텍처 다이어그램](#2-전체-아키텍처-다이어그램)
3. [핵심 구성 요소 상세](#3-핵심-구성-요소-상세)
   - 3.1 SupervisorAgentV2 (오케스트레이터)
   - 3.2 Skill 레이어
   - 3.3 하위 에이전트 (구버전 v1)
   - 3.4 SecurityAgent (가드레일)
   - 3.5 ResponseFormatter
4. [LangChain 주요 개념 매핑](#4-langchain-주요-개념-매핑)
5. [데이터 흐름 상세](#5-데이터-흐름-상세)
6. [RAG 시스템](#6-rag-시스템)
7. [현재 시스템의 한계점](#7-현재-시스템의-한계점)

---

## 1. 시스템 개요

이 시스템은 산업 현장의 **안전 모니터링 CCTV 데이터**를 AI가 자동 분석하고, 사용자(안전 관리자)의 자연어 질의에 답변하는 멀티에이전트 시스템입니다.

### 제공 기능
| 기능 | 예시 질의 |
|------|-----------|
| 이벤트 데이터 조회 | "CAM-001에서 발생한 이벤트 보여줘" |
| 안전 통계 분석 | "지난 7일간 가장 위험한 구역은?" |
| 보고서 생성 | "오늘 일일 보고서 작성해줘" |
| 이미지 분석 | "이 CCTV 사진에서 PPE 미착용자 찾아줘" |
| 지식 기반 Q&A | "낙상 사고 시 즉각 조치 방법은?" |

### 기술 스택
```
LLM:            Google Gemma-3-27B-it (via Gemini API)
Vision LLM:     Gemini-2.5-Flash-Image
Framework:      LangChain 0.1.0
Vector DB:      ChromaDB 0.4.22
Embedding:      sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
Backend API:    FastAPI 0.109.0
Auth:           JWT (python-jose) + SQLite
```

---

## 2. 전체 아키텍처 다이어그램

```
┌────────────────────────────────────────────────────────────┐
│                    FastAPI Server (app.py)                   │
│  POST /api/query          POST /api/multimodal-query        │
└─────────────────────────────┬──────────────────────────────┘
                              │ user_input (+ images)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│               SecurityAgent (입구 가드레일)                   │
│   1단계: 규칙 기반 (금지 키워드, 길이 제한)                   │
│   2단계: LLM 기반 (프롬프트 인젝션, 의도 분석)               │
└─────────────────────────────┬───────────────────────────────┘
                              │ is_safe = True
                              ▼
┌──────────────────────────────────────────────────────────────┐
│              SupervisorAgentV2 (오케스트레이터)               │
│                                                              │
│  ┌─────────────────┐    ┌──────────────────────────────┐   │
│  │  quick_route()  │    │        llm_route()            │   │
│  │  (규칙 기반)    │    │  (LLM이 JSON으로 라우팅 결정) │   │
│  │  키워드 매핑    │    │  single_step / multi_step     │   │
│  └────────┬────────┘    └──────────────┬───────────────┘   │
│           └──────────────┬─────────────┘                    │
│                          ▼                                   │
│              _execute_skill() / _execute_multi_step()        │
└──────────────────────────┬───────────────────────────────────┘
                           │
         ┌─────────────────┼─────────────────────┐
         ▼                 ▼                      ▼
┌─────────────┐   ┌──────────────────┐   ┌─────────────────┐
│data_analytics│   │knowledge_mgmt    │   │report_generation│
│   Skill     │   │   Skill (RAG)    │   │    Skill        │
└─────────────┘   └──────────────────┘   └─────────────────┘
         ▼                 ▼                      ▼
┌──────────────────────────────────────────────────────────────┐
│                  ResponseFormatter                            │
│  원시 Dict 결과 → 사용자 친화적 자연어 응답                  │
└──────────────────────────────────────────────────────────────┘
```

---

## 3. 핵심 구성 요소 상세

### 3.1 SupervisorAgentV2 — 오케스트레이터

**파일**: `agents/supervisor_v2.py`

Supervisor는 전체 시스템의 두뇌 역할로, 사용자 요청을 받아 적합한 Skill로 위임합니다.

#### 라우팅 2단계 전략

**1단계: quick_route() — 규칙 기반 빠른 라우팅 (LLM 호출 없음)**

```python
keywords_map = {
    'data_analytics': ['통계', '분석', '추세', '위험도'],
    'report_generation': ['보고서', '조치', '방안', '대응'],
    'knowledge_management': ['검색', '법규', '알려', '설명'],
    'vision_analysis': ['이미지', '사진', 'PPE', '착용']
}
```

- 단순 키워드 매칭으로 대부분의 요청을 LLM 없이 처리
- 속도: ~0ms (즉시)
- 단점: 복잡한 문맥 파악 불가

**2단계: llm_route() — LLM 기반 정밀 라우팅**

quick_route가 실패(None 반환)한 경우에만 실행됩니다.

```python
# LLM에게 라우팅을 JSON 형태로 결정하도록 요청
routing_prompt = """
사용자 요청: {user_input}

사용 가능한 Skills: data_analytics, report_generation, 
                     knowledge_management, vision_analysis

응답 형식 (JSON만):
{
  "skill": "data_analytics",
  "task": "구체적인 작업 설명",
  "multi_step": false
}
"""
```

- LLM이 JSON을 생성하면 `re.search(r'\{[\s\S]*\}', ...)` 로 파싱
- 복잡한 요청은 `multi_step: true` + `steps: [...]` 형태로 반환

#### 멀티스텝 실행 방식

```python
# 예: "가장 위험한 구역의 대응 방안 알려줘"
# LLM 라우팅 결과:
{
  "multi_step": true,
  "steps": [
    {"skill": "data_analytics", "task": "위험 구역 분석"},
    {"skill": "report_generation", "task": "대응 방안 작성"}
  ]
}

# 실행 흐름:
Step 1: data_analytics("위험 구역 분석") → result1
Step 2: report_generation("대응 방안 작성\n\n이전 단계 결과:\n" + result1)
```

> ⚠️ **현재 방식의 핵심 한계**: 단순히 이전 결과를 문자열로 붙여서 다음 단계에 전달합니다. 구조화된 상태 공유가 없습니다.

---

### 3.2 Skill 레이어 — 도메인 전문가

**폴더**: `skills/`

각 Skill은 특정 도메인의 전문 작업을 처리하는 독립 모듈입니다.

#### BaseSkill — 모든 Skill의 공통 인터페이스

```python
class BaseSkill(ABC):
    def __init__(self):
        self.metadata = self._load_metadata()   # SkillMetadata (name, version, tags)
        self.tools = self._initialize_tools()   # 내부에서 쓸 도구 (LLM, RAG 등)
        self.prompts = self._load_prompts()     # prompts/*.txt 파일 자동 로드
        self.config = self._load_config()       # config.yaml 자동 로드

    @abstractmethod
    def execute(self, task: str, context: dict) -> dict:
        """핵심 실행 메서드 — 반드시 구현 필요"""
        pass
```

#### 구현된 4개 Skill 상세

**① data_analytics** (`skills/data_analytics/skill.py`)
- 역할: 이벤트 통계 계산, 추세 분석, 위험도 평가
- 주요 tasks: `calculate_statistics`, `analyze_trend`, `assess_risk`, `find_top_cameras`
- 데이터 소스: `data/events.json` (JSON 파일 직접 읽기)

**② knowledge_management** (`skills/knowledge_management/skill.py`)
- 역할: RAG 기반 지식 검색 및 Q&A
- 주요 tasks: `search_knowledge`, `get_action_guide`, `answer_question`, `search_regulations`
- 특이점: 내부적으로 `RAGSystem`을 초기화하여 ChromaDB 벡터 DB에 접근

```python
# 답변 생성 흐름 (RAG + LLM)
def _answer_question(self, context):
    # 1. 관련 문서 검색 (ChromaDB 시맨틱 검색)
    docs = rag_system.search(question, k=3)
    # 2. 검색 결과를 컨텍스트로 LLM 호출
    prompt = f"다음 문서를 참고하여 답변: {docs}\n\n질문: {question}"
    answer = llm.invoke(prompt)
    return {"answer": answer.content}
```

**③ report_generation** (`skills/report_generation/skill.py`)
- 역할: 일일/주간 보고서, 조치 방안, 사고 보고서 생성
- 주요 tasks: `generate_daily_report`, `generate_weekly_report`, `generate_action_plan`, `generate_incident_report`
- 특이점: `skills/report_generation/prompts/action_plan.txt` 같은 외부 프롬프트 파일 활용

**④ vision_analysis** (`skills/vision_analysis/skill.py`)
- 역할: CCTV/작업장 이미지에서 안전 위반 사항 감지
- 주요 tasks: `analyze_image`, `detect_ppe`, `compare_images`
- 특이점: `vision_model: gemini-2.5-flash-image` 사용 (멀티모달 LLM)

#### SkillManager — Skill 중앙 레지스트리

```python
class SkillManager:
    def __init__(self):
        self._load_all_skills()  # skills/ 하위 디렉토리 자동 스캔

    def _load_skill(self, skill_name):
        # "data_analytics" → "DataAnalyticsSkill" 클래스명 변환
        class_name = ''.join(w.capitalize() for w in skill_name.split('_')) + 'Skill'
        module = importlib.import_module(f"skills.{skill_name}.skill")
        self.skills[skill_name] = getattr(module, class_name)()

    def execute_skill(self, skill_name, task, context) -> dict:
        skill = self.skills[skill_name]
        skill.validate_input(task, context)
        result = skill.execute(task, context)
        return {'success': True, 'result': result}
```

---

### 3.3 하위 에이전트 (구버전 v1)

**폴더**: `agents/` (query, analysis, report, search, multimodal)

> ℹ️ **현재 미사용**: `supervisor_v2.py`가 Skill 레이어를 직접 호출하므로, v1 에이전트들(QueryAgent 등)은 현재 실질적으로 사용되지 않습니다. 구버전 코드와의 호환성을 위해 남겨두었습니다.

이 에이전트들은 LangChain의 **ReAct 패턴**을 사용합니다.

```python
# QueryAgent 예시 — ReAct 패턴
class QueryAgent:
    def __init__(self):
        self.tools = [get_camera_events, get_all_cameras, ...]
        
        # ReAct 프롬프트: Thought → Action → Observation 사이클
        template = """
        Question: {input}
        Thought: 무엇을 해야 할지 생각
        Action: [tool_names] 중 선택
        Action Input: 도구에 전달할 입력
        Observation: 도구 실행 결과
        ... (반복)
        Final Answer: 최종 답변
        {agent_scratchpad}
        """
        
        # LangChain 표준 ReAct 에이전트 생성
        self.agent = create_react_agent(llm, tools, prompt)
        self.agent_executor = AgentExecutor(agent, tools, max_iterations=5)
```

#### ReAct 패턴이란?
```
ReAct = Reasoning + Acting

LLM이 "생각(Thought) → 행동(Action) → 관찰(Observation)" 을 반복하며
적절한 도구를 선택하고 실행하는 패턴

예:
Thought: 사용자가 CAM-001 이벤트를 원하니 get_camera_events 도구를 써야겠다
Action: get_camera_events
Action Input: {"camera_id": "CAM-001"}
Observation: [{"event_type": "NO_HELMET", ...}, ...]
Thought: 이제 최종 답변을 줄 수 있다
Final Answer: CAM-001에서 3건의 이벤트가 발생했습니다...
```

---

### 3.4 SecurityAgent — 입구 가드레일

**파일**: `agents/security_agent.py`

모든 API 요청은 Supervisor 실행 전에 SecurityAgent를 통과해야 합니다.

```
요청 수신
   │
   ▼
[1단계] 규칙 기반 검사 (즉시, LLM 없음)
   ├─ 금지 키워드 포함 여부 ("이전 지시 무시", "시스템 프롬프트" 등 15개)
   ├─ 입력 길이 > 5,000자 여부
   └─ 차단 시 즉시 반환 (LLM 호출 절약)
   │
   ▼
[2단계] LLM 기반 의도 분석 (~ 1~2초)
   ├─ 프롬프트 인젝션 판단
   ├─ 역할 연기 강요 판단
   ├─ 비업무 요청 판단
   └─ 응답: "SAFE" 또는 "UNSAFE: [이유]"
```

> **설계 포인트**: LLM 오류 발생 시 `가용성 우선` 정책으로 SAFE 처리합니다. 보안 우선이 필요하다면 UNSAFE로 전환할 수 있습니다.

---

### 3.5 ResponseFormatter — 응답 후처리

**파일**: `utils/response_formatter.py`

Skill이 반환하는 원시 `Dict` 결과를 사용자 친화적인 자연어로 변환합니다.

```python
# 변환 우선순위
결과 Dict 수신
   │
   ▼
[1순위] 특정 키 직접 추출: 'answer', 'action_plan', 'report', 'guide' 등
   │    → 이 키가 있으면 마크다운 제거 후 바로 반환
   │
   ▼
[2순위] LLM 포맷팅: JSON 덤프 → LLM에게 자연어로 변환 요청
   │    → 마크다운(**볼드**, # 헤딩 등) 사용 금지 지시
   │
   ▼
[3순위] 폴백: 기본 key: value 텍스트 변환
```

> **왜 마크다운을 제거하나?** 현재 프론트엔드가 마크다운 렌더링을 지원하지 않아 `**볼드**`가 그대로 노출됩니다.

---

## 4. LangChain 주요 개념 매핑

현재 시스템에서 실제로 사용 중인 LangChain 컴포넌트입니다.

### 4.1 ChatGoogleGenerativeAI (LLM 호출)

```python
from langchain_google_genai import ChatGoogleGenerativeAI

llm = ChatGoogleGenerativeAI(
    model="gemma-3-27b-it",
    temperature=0.0,
    google_api_key=settings.google_api_key
)

# 사용 방법: 문자열 프롬프트를 직접 전달
response = llm.invoke("사용자 요청: ...")
text = response.content  # AIMessage.content 에서 텍스트 추출
```

### 4.2 PromptTemplate (프롬프트 관리)

```python
from langchain.prompts import PromptTemplate

template = "질문: {input}\n생각: {agent_scratchpad}"
prompt = PromptTemplate.from_template(template)
# {input}, {agent_scratchpad} 같은 변수를 런타임에 채워줌
```

### 4.3 create_react_agent + AgentExecutor

```python
from langchain.agents import AgentExecutor, create_react_agent

# ReAct 에이전트 = LLM + 도구 목록 + 프롬프트
agent = create_react_agent(llm=llm, tools=tools, prompt=prompt)

# AgentExecutor = 에이전트를 루프 실행, 도구 호출 관리
executor = AgentExecutor(
    agent=agent,
    tools=tools,
    max_iterations=5,           # 최대 Thought-Action 반복 횟수
    handle_parsing_errors=True  # 파싱 실패 시 에러 대신 재시도
)
result = executor.invoke({"input": user_query})
```

### 4.4 @tool 데코레이터

```python
from langchain.tools import tool

@tool
def get_camera_events(camera_id: str) -> str:
    """특정 카메라의 이벤트를 조회합니다."""
    # 함수 로직
    return json.dumps(events)
```

LLM이 "이 함수는 어떤 입력을 받고 무엇을 하는지" docstring을 보고 사용 여부를 결정합니다.

### 4.5 Document + VectorStore (RAG)

```python
from langchain.schema import Document
from langchain_community.vectorstores import Chroma

# Document = 텍스트 + 메타데이터 단위
doc = Document(
    page_content="안전모 미착용 시 대응 절차...",
    metadata={"event_type": "NO_HELMET", "source_file": "NO_HELMET.md"}
)

# ChromaDB에 저장 (임베딩 자동 생성)
vectorstore = Chroma.from_documents(docs, embedding_function)

# 유사 문서 검색
results = vectorstore.similarity_search("안전모 관련 조치", k=3)
```

---

## 5. 데이터 흐름 상세

### 단일 요청 흐름 (예: "지난 7일 통계 분석해줘")

```
1. POST /api/query { "query": "지난 7일 통계 분석해줘", "session_id": "abc123" }

2. SecurityAgent.check_safety("지난 7일 통계 분석해줘")
   → 1단계 (규칙): PASS (금지 키워드 없음)
   → 2단계 (LLM): SAFE
   → is_safe = True

3. SupervisorAgentV2.execute("지난 7일 통계 분석해줘")
   → quick_route() 실행
   → "통계", "분석" 키워드 매칭 → skill = "data_analytics"

4. _execute_skill("data_analytics", "지난 7일 통계 분석해줘", ...)
   → _determine_task(): "통계" 키워드 → task = "calculate_statistics"
   → context = {"query": "지난 7일 통계 분석해줘"}

5. SkillManager.execute_skill("data_analytics", "calculate_statistics", context)
   → DataAnalyticsSkill.execute("calculate_statistics", context)
   → data/events.json 읽기 → 통계 계산
   → return {"statistics": {"total": 42, "by_type": {...}, ...}}

6. ResponseFormatter.format_response(raw_result, ...)
   → 'statistics' 키 없음 → LLM 포맷팅 호출
   → LLM: "지난 7일간 총 42건의 이벤트가 발생했습니다..."
   → return "지난 7일간 총 42건..."

7. QueryResponse { "response": "지난 7일간 총 42건...", "session_id": "abc123" }
```

### 멀티스텝 흐름 (예: "가장 위험한 구역의 대응 방안 알려줘")

```
(생략된 보안 검사 이후)

3. SupervisorAgentV2.execute(...)
   → quick_route() → None (명확한 키워드 없음)
   → llm_route() → {"multi_step": true, "steps": [
       {"skill": "data_analytics", "task": "위험 구역 파악"},
       {"skill": "report_generation", "task": "대응 방안 작성"}
     ]}

4. _execute_multi_step() 실행:
   Step 1: data_analytics → result1 = "CAM-003이 가장 위험, 주간 12건..."
   Step 2: context = "대응 방안 작성\n\n이전 단계 결과:\nCAM-003이..."
           report_generation(context) → result2 = "CAM-003 대응 방안: 1. 즉시..."

5. return result2 (마지막 단계 결과)
```

---

## 6. RAG 시스템

**파일**: `utils/rag_system.py` (KnowledgeManagementSkill 내부에서 사용)

### 구성

```
data/knowledge_base/
├── NO_HELMET.md        → 안전모 미착용 대응 가이드
├── FALL_DETECTED.md    → 낙상 사고 대응 가이드
├── FIRE_HAZARD.md      → 화재 위험 대응 가이드
└── ...

↓ (초기화 시 임베딩 생성 + ChromaDB 저장)

data/vector_store/      → ChromaDB 영구 저장소
```

### 초기화 흐름

```python
rag_system.initialize(force_rebuild=False)
# 1. knowledge_base/*.md 파일 읽기
# 2. TextSplitter로 청크 분할 (chunk_size=500, overlap=50)
# 3. paraphrase-multilingual-MiniLM-L12-v2 임베딩 생성
# 4. ChromaDB에 벡터 + 메타데이터 저장
# force_rebuild=False: 기존 벡터 재사용 (빠른 시작)
```

### 검색 흐름

```python
# 질문: "낙상 사고 시 즉각 조치는?"

# 1. 질문을 동일 임베딩 모델로 벡터화
# 2. ChromaDB에서 코사인 유사도로 k개 문서 검색
results = vectorstore.similarity_search(question, k=3)

# 3. 검색 결과를 LLM 컨텍스트로 제공
# 4. LLM이 문서 기반으로 답변 생성 (Grounded Generation)
```

### 지식 베이스 특이점

각 `.md` 파일에는 다음 구조가 포함됩니다:
- 이벤트 개요 및 정의
- 즉각 조치 절차 (단계별)
- 관련 법규 (산업안전보건법 등)
- 예방 대책

---

## 7. 현재 시스템의 한계점

### 7.1 상태 관리 없음

```python
# 현재: 이전 단계 결과를 단순 문자열로 붙임
task_with_context = f"{task}\n\n이전 단계 결과:\n{prev_result}"

# 문제: 구조화된 데이터가 사라짐, 각 단계가 이전 결과의 구조를 모름
```

### 7.2 대화 메모리 없음

```python
# 각 API 호출은 완전히 독립적
# "방금 말한 CAM-003 보고서 만들어줘" → CAM-003을 모름
# session_id는 받지만 실제로 저장/조회 로직이 없음
```

### 7.3 병렬 실행 불가

```python
# data_analytics와 knowledge_management가 독립적인데도
# 반드시 순차 실행 (Step 1 끝나야 Step 2 시작)
for step in steps:
    result = execute_skill(step)  # 순차
```

### 7.4 오류 복원 없음

```python
# Skill 실패 시 단순 오류 메시지 반환
# 자동 재시도, 대체 Skill 선택 등 없음
try:
    result = skill.execute(task, context)
except Exception as e:
    return f"오류: {str(e)}"  # 그냥 끝
```

### 7.5 라우팅 불안정

```python
# quick_route의 키워드 매칭이 너무 단순
# "분석"이라는 단어 하나로 data_analytics OR vision_analysis 동시 매칭 가능
# 실제로 vision_analysis 키워드에도 '분석'이 있음
```

---

> 📌 다음 문서: `02_migration_plan.md` — LangGraph 기반으로의 마이그레이션 계획 및 작업 프로세스
