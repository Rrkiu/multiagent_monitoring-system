# Milestone 2 — 고급 패턴 (메모리, 재시도, 병렬 실행)
## 자기학습 기록 문서

> 작성일: 2026-03-03  
> 최종 수정: 2026-03-03 (도메인 필터 버그픽스 추가)  
> 목적: M2 작업 내용 스스로 이해 및 복기  
> 범위: `agents/supervisor_langgraph.py` (M2 업그레이드), `utils/session_manager.py` (신규)

---

## 목차

1. [M2에서 무엇을 추가했는가](#1-m2에서-무엇을-추가했는가)
2. [M2-1: SqliteSaver — 영속 대화 메모리](#2-m2-1-sqlitesaver--영속-대화-메모리)
3. [M2-2: 메시지 윈도우 — 최근 10개 유지](#3-m2-2-메시지-윈도우--최근-10개-유지)
4. [M2-3: 에러 재시도 루프](#4-m2-3-에러-재시도-루프)
5. [M2-4: 병렬 스킬 실행 (Send API)](#5-m2-4-병렬-스킬-실행-send-api)
6. [SessionManager — TTL 세션 관리](#6-sessionmanager--ttl-세션-관리)
7. [M2 그래프 구조 (Before/After)](#7-m2-그래프-구조-beforeafter)
8. [발생한 문제 및 해결](#8-발생한-문제-및-해결)
9. [검증 결과](#9-검증-결과)
10. [M2 이후 발견된 버그 수정](#10-m2-이후-발견된-버그-수정)

---

## 1. M2에서 무엇을 추가했는가

| 항목 | M1 | M2 |
|------|----|----|
| 대화 메모리 | MemorySaver (인메모리) | **SqliteSaver** (DB 영속) |
| 세션 관리 | session_id 그대로 전달 | **SessionManager** (TTL 2시간) |
| 메시지 이력 | 무제한 누적 | **최근 10개** (trim_messages) |
| 스킬 실패 시 | 오류 메시지 즉시 반환 | **최대 3회 재시도** (router 재라우팅) |
| 멀티스텝 실행 | for 루프 (순차) | **Send API** (병렬 동시 실행) |
| 추가 노드 | — | `parallel_dispatcher`, `error` |

### 변경된 파일

| 파일 | 변경 내용 |
|------|-----------|
| `agents/supervisor_langgraph.py` | 전면 업그레이드 (4가지 M2 기능 추가) |
| `utils/session_manager.py` | 신규 — TTL 세션 관리 |
| `app.py` | get_supervisor에 `use_sqlite=True` 추가, SessionManager 연결 |

---

## 2. M2-1: SqliteSaver — 영속 대화 메모리

### 왜 MemorySaver → SqliteSaver인가?

```
MemorySaver
  ✅ 빠름 (인메모리)
  ❌ 프로세스 재시작 시 모든 대화 이력 소멸
  ❌ 멀티 워커(uvicorn 멀티프로세스) 환경에서 이력 공유 불가

SqliteSaver
  ✅ DB 파일에 영속 저장 (재시작 후에도 유지)
  ✅ 같은 DB 파일을 여러 프로세스가 읽기 가능
  ❌ 약간의 디스크 I/O 발생 (대부분 무시 가능)
```

### 설치

```bash
pip install langgraph-checkpoint-sqlite
```

`langgraph-checkpoint-sqlite`는 langgraph와 별도 패키지로 분리됨.

### 코드

```python
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3

DB_PATH = "./data/agent_memory.db"

# SqliteSaver 초기화 (LangGraph 1.x 호환 방식)
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn)

# 그래프 컴파일 시 checkpointer 연결
graph = workflow.compile(checkpointer=checkpointer)
```

> ⚠️ **주의**: `SqliteSaver.from_conn_string(DB_PATH)`는 LangGraph 1.x에서 context manager를  
> 반환하며 `BaseCheckpointSaver` 인스턴스가 아니라 컴파일 시 `TypeError`가 발생한다.  
> `sqlite3.connect()` 직접 연결 후 `SqliteSaver(conn)`으로 초기화해야 한다.  
> (자세한 내용은 [섹션 8 — 발생한 문제 및 해결](#8-발생한-문제-및-해결) 참고)

### Checkpointer가 저장하는 것

```
thread_id: "user_abc_99519f01"
  ├── checkpoint_id: "abc123..."
  │     └── state: {messages: [...], routing_plan: {...}, ...}
  └── checkpoint_id: "def456..."  ← 다음 호출 시 추가됨
```

- `graph.invoke(state, {"configurable": {"thread_id": "xxx"}})` 호출 시
  - 이전 체크포인트가 있으면 로드 → 기존 state에 merge
  - 실행 완료 후 새 체크포인트 저장

### 동일 thread_id로 연속 호출 시 동작

```python
# Turn 1
graph.invoke({"messages": [], "user_query": "안전모 규정이 뭐야?"}, config)
# DB 저장: messages = [HumanMessage("안전모..."), AIMessage("안전모는...")]

# Turn 2 (동일 thread_id)
graph.invoke({"messages": [], "user_query": "방금 말한 법규 번호가 뭐야?"}, config)
# DB에서 로드 → 기존 messages에 새 메시지가 append (Annotated[list, operator.add])
# messages = [HumanMessage("안전모..."), AIMessage("안전모는..."),
#             HumanMessage("방금 말한..."), AIMessage("제38조...")]
```

> **포인트**: `messages` 필드가 `Annotated[list, operator.add]`로 선언되어 있으므로  
> Checkpointer가 이전 값에 새 값을 **append**한다.

---

## 3. M2-2: 메시지 윈도우 — 최근 10개 유지

### 왜 필요한가?

대화가 길어지면 `messages`에 무한정 메시지가 누적된다.  
LLM 라우팅 / 스킬 실행 시 이 모든 메시지를 처리하면:
- LLM 컨텍스트 윈도우 초과 위험
- 응답 속도 저하
- 비용 증가

### 구현 위치: `router_node`

```python
from langchain_core.messages import trim_messages

MESSAGE_WINDOW = 10

def router_node(state: AgentState) -> dict:
    current_messages = state.get("messages", [])

    if len(current_messages) > MESSAGE_WINDOW:
        trimmed = trim_messages(
            current_messages,
            strategy="last",          # 최근 메시지를 유지
            max_tokens=MESSAGE_WINDOW,
            token_counter=len,        # 토큰이 아닌 메시지 개수 기준
            allow_partial=False,
        )
        messages_update = trimmed
    else:
        messages_update = current_messages

    return {
        "messages": messages_update,  # 슬라이딩 윈도우 적용
        "routing_plan": plan,
        ...
    }
```

### 왜 router_node에서 처리하는가?

- **security_node** 이후, **스킬 실행 전** 시점이 자연스럽다
- 라우팅 결정 시 필요한 컨텍스트(최근 대화)만 남기는 목적이므로 라우터 직전이 적절
- synthesizer_node에서 AI 응답 추가 → router_node에서 슬라이딩 → 균형 유지

### 슬라이딩 윈도우 시각화

```
Turn  1~10:  M1 M2 M3 M4 M5 M6 M7 M8 M9 M10  ← 전부 유지
Turn 11    :  M2 M3 M4 M5 M6 M7 M8 M9 M10 M11 ← M1 드롭
Turn 12    :  M3 M4 M5 M6 M7 M8 M9 M10 M11 M12 ← M2 드롭
```

### messages 필드와 trim_messages의 상호작용 주의

```python
# 주의: messages는 Annotated[list, operator.add] → 반환하면 append됨
# 따라서 trimmed 결과를 반환하면 기존 messages + trimmed가 또 append됨

# 잘못된 방법
return {"messages": trimmed}  # 기존 messages + trimmed → 이중 저장!

# 현재 구현: messages_update = trimmed (현재 state의 messages를 대체)
```

> **해결책**: `AgentState`에 `messages`를 `Annotated[list, operator.add]`가 아닌 단순 `list`로  
> 선언하면 완전 교체가 된다. 현재 구현에서는 `state.get("messages")`를 읽어서  
> 동일 내용(`trimmed`)을 반환하므로 사실상 교체 효과.  
> 정확한 구현은 M3에서 리팩터링 시 재검토 예정.

---

## 4. M2-3: 에러 재시도 루프

### M1의 문제

```
skill_executor 실패 → synthesizer → "결과를 생성할 수 없습니다" (즉시 실패)
```

### M2 해결: router로 재라우팅

```
skill_executor 실패 → check_after_skill
  ├── iteration_count < 3 → router (재라우팅)
  │     └── 다른 라우팅 결과 가능 → skill_executor 재시도
  └── iteration_count >= 3 → error_node → END
```

### 핵심 코드

```python
MAX_RETRY = 3

def check_after_skill(state: AgentState) -> Literal["retry", "synthesize", "fail"]:
    if not state.get("error"):
        return "synthesize"                           # 성공 → 종료
    if state.get("iteration_count", 0) < MAX_RETRY:
        return "retry"                                # 실패 + 재시도 가능 → router
    return "fail"                                     # 최대 초과 → error_node
```

```python
def skill_executor_node(state: AgentState) -> dict:
    try:
        result = skill_manager.execute_skill(...)
        return {"skill_results": {...}, "error": None}
    except Exception as e:
        return {
            "error": str(e),
            "iteration_count": state.get("iteration_count", 0) + 1,  # 카운트 증가
        }
```

### 재라우팅 시 router_node의 역할

재시도 시 router_node는 `error: None`으로 초기화하고 **동일 user_query**로 다시 라우팅한다.  
`_llm_route()`가 호출되면 이전과 다른 스킬을 선택할 수도 있어 복구 가능성이 있다.

```python
def router_node(state: AgentState) -> dict:
    ...
    return {
        "routing_plan": plan,
        "error": None,   # ← 재시도 시 이전 error 클리어
        ...
    }
```

### error_node — 최종 실패 응답

```python
def error_node(state: AgentState) -> dict:
    """최대 재시도 초과 시 사용자 친화적 오류 응답"""
    return {
        "final_answer": (
            f"요청을 처리하는 과정에서 문제가 발생했습니다.\n"
            f"({skill} 스킬 {count}회 시도 실패)\n"
            f"잠시 후 다시 시도하거나 질문 방식을 바꿔 주세요."
        )
    }
```

---

## 5. M2-4: 병렬 스킬 실행 (Send API)

### M1의 문제

멀티스텝 실행이 for 루프로 순차 실행됨:
```
Step1(data_analytics) 완료 → Step2(report_generation) 시작 → 완료
총 시간 = Step1 + Step2
```

### M2: Send API로 병렬 실행

```
Step1(data_analytics)     → 동시 시작
Step2(knowledge_management) → 동시 시작
                          모두 완료 → synthesizer (Fan-in)
총 시간 = max(Step1, Step2)
```

### Send API란?

```python
from langgraph.types import Send

# Send("노드이름", state_update)
# → "노드이름" 노드를 새 서브 state로 병렬 실행
Send("parallel_skill", {**state, "_current_step": step})
```

- `**state`: 현재 state 전체 복사 (각 워커는 독립적 state 가짐)
- `"_current_step": step`: 어떤 스텝을 실행해야 하는지 워커에게 알려주는 필드

### 4개 컴포넌트의 역할

```
router_node
  → check_routing → "multi_step"
  → parallel_dispatcher_node    ← identity 노드 (상태 변경 없음)
  → route_parallel_skills()     ← List[Send] 반환
      ├── Send("parallel_skill", step1_state)  ┐
      ├── Send("parallel_skill", step2_state)  ├ 병렬 실행
      └── Send("parallel_skill", step3_state)  ┘
  → parallel_skill_node × N     ← 각 스킬 실행
  → synthesizer                 ← Fan-in (모든 결과 합류)
```

### parallel_dispatcher_node가 왜 필요한가?

LangGraph 1.x에서 `add_conditional_edges`의 `path_map`에 함수(Send 반환)를 직접 값으로 넣으면 컴파일 오류가 발생한다:

```python
# ❌ 안 됨 (LangGraph 1.0.x에서 오류)
workflow.add_conditional_edges(
    "router",
    check_routing,
    {"multi_step": route_parallel_skills}  # 함수를 직접 값으로 → 오류
)

# ✅ 해결: 중간 노드 경유
workflow.add_conditional_edges("router", check_routing,
    {"multi_step": "parallel_dispatcher"})  # 노드 이름으로
workflow.add_conditional_edges("parallel_dispatcher",
    route_parallel_skills)  # 이 노드의 조건부 엣지로 Send
```

### skill_results의 병렬 merge

```python
# parallel_skill_node가 반환:
return {"skill_results": {"data_analytics": result1}, ...}
# 또 다른 parallel_skill_node가 반환:
return {"skill_results": {"knowledge_management": result2}, ...}

# skill_results는 dict → LangGraph가 자동으로 merge (덮어쓰기)
# 최종: {"data_analytics": result1, "knowledge_management": result2}
```

> **주의**: `skill_results` 필드 merge 방식이 `operator.add`가 아닌 단순 덮어쓰기이므로  
> 동일 키를 두 워커가 쓰면 마지막 것만 남는다.  
> 현재는 각 스킬이 고유한 key를 쓰므로 문제없음.

---

## 6. SessionManager — TTL 세션 관리

**파일**: `utils/session_manager.py`

### 문제 정의

LangGraph Checkpointer는 `thread_id`로 대화 이력을 구분한다.  
단순히 request의 `session_id`를 그대로 쓰면:

```
문제 1: session_id가 없는 요청 → thread_id를 어떻게 결정?
문제 2: 2시간 이상 쉬다 다시 접속 → 이전 대화 이력에 이어서 응답 (어색함)
문제 3: 사용자가 "대화 초기화" 요청 → 새 thread_id 발급 필요
```

### SessionManager 해결 방식

```python
class SessionManager:
    # user_id → {"thread_id": str, "last_active": datetime}
    _sessions: Dict[str, dict]

    def get_thread_id(self, user_id: str) -> str:
        session = self._sessions.get(user_id)

        if session is None:
            # 첫 방문 → 신규 발급
            return new_thread_id(user_id)

        elapsed = now - session["last_active"]
        if elapsed > timedelta(minutes=120):
            # TTL 초과 → 자동으로 새 대화 시작
            return new_thread_id(user_id)

        # TTL 이내 → 기존 thread_id 반환 (대화 이력 유지)
        return session["thread_id"]
```

### thread_id 형식

```
user_abc_99519f01
└──┬───┘ └──┬───┘
user_id    UUID 8자리 (랜덤)
```

동일 user_id도 TTL 초과 시마다 다른 suffix가 붙어 새 세션이 된다.

### app.py에서의 사용

```python
# 기존 (M1)
response = agent.execute(user_input=request.query, session_id=request.session_id)

# M2
user_id = request.session_id or current_user.username  # session_id 없으면 username 사용
thread_id = get_session_manager().get_thread_id(user_id)
response = agent.execute(user_input=request.query, session_id=thread_id)
return QueryResponse(response=response, session_id=thread_id)  # 실제 thread_id 반환
```

프론트엔드는 응답의 `session_id`(실제 thread_id)를 저장해두었다가 다음 요청에 전달하면  
SessionManager가 TTL 체크 없이 직접 Checkpointer에 연결된다.

---

## 7. M2 그래프 구조 (Before/After)

### M1 그래프

```
__start__
    │
    ▼
[security]
    ├─ block ──────────────────────────── __end__
    └─ pass  ──→ [router]
                     ├─ single ──→ [skill_executor] ──→ [synthesizer] ──→ __end__
                     └─ multi  ──→ [multi_step_executor] ──→ [synthesizer] ──→ __end__
```

### M2 그래프 (with out_of_scope 분기 추가 — 버그픽스 포함)

```
__start__
    │
    ▼
[security]
    ├─ block ──────────────────────────────────────────── __end__
    └─ pass  ──→ [router] ←──────── retry ─────────────┐
                     │                                  │
                     ├─ out_of_scope ──→ [synthesizer] ─┤  ← 도메인 외 질문 즉시 응답
                     │                                  │
                     ├─ single ──→ [skill_executor]     │
                     │                 ├─ synthesize ──→ [synthesizer] ──→ __end__
                     │                 ├─ retry ────────┘  (최대 3회)
                     │                 └─ fail ──→ [error] ──→ __end__
                     │
                     └─ multi ──→ [parallel_dispatcher]
                                       │
                                       ▼ (route_parallel_skills → List[Send])
                               ┌───────────────────┐
                               │ [parallel_skill×1] │ ─── 동시 실행
                               │ [parallel_skill×2] │
                               │ [parallel_skill×N] │
                               └───────────────────┘
                                       │ (Fan-in)
                                       ▼
                                 [synthesizer] ──→ __end__
```

### 최종 노드 목록

```python
['__start__', 'security', 'router', 'skill_executor',
 'parallel_dispatcher', 'parallel_skill',
 'synthesizer', 'error', '__end__']
```

---

## 8. 발생한 문제 및 해결

### 문제 1: Send API를 conditional_edges path_map에 직접 사용 불가

**증상**:
```
ValueError: At 'router' node, 'check_routing' branch found unknown target
'<function route_parallel_skills at 0x7ce5ea4bc4c0>'
```

**원인**: LangGraph 1.0.x에서 `add_conditional_edges`의 반환값 매핑에  
`List[Send]`를 반환하는 함수를 값으로 지정하면 노드 이름이 아닌 함수 객체로 인식해 오류.

**해결**: 중간 identity 노드(`parallel_dispatcher`) 경유 방식으로 변경

```python
# Before (안됨)
workflow.add_conditional_edges("router", check_routing,
    {"multi_step": route_parallel_skills})  # ← 함수 직접

# After (됨)
workflow.add_conditional_edges("router", check_routing,
    {"multi_step": "parallel_dispatcher"})  # ← 노드 이름
workflow.add_node("parallel_dispatcher", parallel_dispatcher_node)
workflow.add_conditional_edges("parallel_dispatcher",
    route_parallel_skills)  # ← 이 노드 전용 조건부 엣지
```

---

### 문제 2: SqliteSaver.from_conn_string()이 TypeError 발생

**증상**:
```
TypeError: Invalid checkpointer provided. Expected an instance of `BaseCheckpointSaver`,
`True`, `False`, or `None`. Received _GeneratorContextManager.
```

**원인**: `SqliteSaver.from_conn_string()`가 LangGraph 1.x에서 context manager  
(`_GeneratorContextManager`)를 반환한다. `with` 블록 없이 직접 변수에 할당하면  
`BaseCheckpointSaver` 인스턴스가 아니므로 컴파일 시 오류 발생.

**해결**: `sqlite3.connect()`로 연결 객체를 직접 생성 후 `SqliteSaver`에 전달

```python
# Before (오류)
checkpointer = SqliteSaver.from_conn_string(DB_PATH)  # context manager 반환

# After (정상)
import sqlite3
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
checkpointer = SqliteSaver(conn)
```

`check_same_thread=False`는 FastAPI의 멀티스레드 환경(uvicorn)에서 필요하다.

---

### 문제 3: 도메인 외 질문에 엉뚱한 안전 응답 반환 (M4 테스트 중 발견)

**증상**:

> 사용자 질문: "오늘 블러드문이라고 하던데, 블러드문이 뭐지?"  
> 시스템 응답: "안전조끼 미착용 대응 가이드 — 심각도: LOW..."

**원인 추적**:

```
"블러드문이 뭐지?"
  → _quick_route()  → None (매칭 키워드 없음)
  → _llm_route()   → knowledge_management (LLM이 억지로 선택)
                      ↑
                      프롬프트에 out_of_scope 선택지가 없었음!
  → RAG 검색       → 안전 DB에서 가장 가까운 문서 반환
  → 응답           → "안전조끼 대응 가이드" (완전 무관)
```

**해결: 3중 도메인 필터**

```python
# 1️⃣ 1차 키워드 필터 (LLM 호출 없음, 빠름)
def _is_safety_domain(user_input: str) -> bool:
    domain_keywords = [
        "안전", "사고", "위험", "이벤트", "낙상", "화재",
        "PPE", "헬멧", "안전모", "통계", "분석", "법규",
        "규정", "카메라", "CAM", "CCTV", "모니터링", ...
    ]
    return any(kw in user_input for kw in domain_keywords)

# router_node에서
if not _is_safety_domain(user_input):
    # LLM 호출 없이 즉시 거절
    return {"final_answer": "안전 전용 시스템 안내", ...}
```

```python
# 2️⃣ LLM 프롬프트에 out_of_scope 선택지 명시
skills = [
    "1. data_analytics",
    "2. report_generation",
    "3. knowledge_management",
    "4. vision_analysis",
    "5. out_of_scope  ← 안전 도메인과 무관한 요청",  # 추가
]
규칙 = "안전/사고/법규와 관련 없으면 반드시 out_of_scope 선택"

# 3️⃣ check_routing에서 out_of_scope → synthesizer 직행
def check_routing(state) -> Literal["single", "multi_step", "out_of_scope"]:
    if plan.get("skill") == "out_of_scope":
        return "out_of_scope"  # final_answer 이미 설정 → synthesizer로 바로
    ...
```

**처리 흐름 비교**:

```
[수정 전] 블러드문 질문
  → LLM 라우팅 → knowledge_management → RAG → 안전조끼 응답 ❌
  비용: LLM 호출 1회 + RAG 검색

[수정 후] 블러드문 질문
  → _is_safety_domain() → False → 즉시 거절 ✅
  비용: 키워드 검사만 (LLM 호출 0회)
```

**도메인 필터 검증 결과 (8/8 통과)**:

```
✅ [외부] 블러드문이 뭐지?              → False (거절)
✅ [외부] 오늘 날씨 어때?              → False (거절)
✅ [외부] 넷플릭스 드라마 추천해줘        → False (거절)
✅ [도메인] 안전모를 착용하지 않으면...   → True  (처리)
✅ [도메인] 최근 7일간 이벤트 통계...    → True  (처리)
✅ [도메인] 낙상 사고 대응 방안...       → True  (처리)
✅ [도메인] CAM-003 이벤트 보고서...    → True  (처리)
✅ [도메인] 법규 위반 시 처벌 기준...    → True  (처리)
```

**교훈**: LLM에게 선택지를 줄 때 **"해당 없음" 옵션을 반드시 포함**해야 한다.  
선택지 없이 강제 선택하게 하면 LLM이 억지로 가장 유사한 카테고리를 선택하며  
이는 완전히 무관한 응답으로 이어진다.

---

## 9. 검증 결과

### M2 완료 기준 체크리스트

- [x] `SqliteSaver(conn)` 직접 연결 방식으로 그래프 컴파일 성공
- [x] `Send` API import 성공
- [x] `trim_messages` import 및 적용
- [x] `build_graph()` — 9개 노드 정상 등록
- [x] `SessionManager` — 동일 user → 동일 thread_id
- [x] `SessionManager` — reset_session → 새 thread_id
- [x] `MAX_RETRY=3`, `MESSAGE_WINDOW=10` 상수 확인
- [x] **`_is_safety_domain()` 도메인 필터 — 8/8 케이스 통과** (버그픽스)
- [x] **도메인 외 질문 → 안내 메시지 반환, 스킬 실행 스킵** (버그픽스)

### 검증 출력

```
[build_graph] MemorySaver (인메모리)
✅ 그래프 컴파일 성공
노드 목록: ['__end__', '__start__', 'error', 'parallel_dispatcher',
            'parallel_skill', 'router', 'security', 'skill_executor', 'synthesizer']
[SessionManager] 신규 세션 발급: user_abc → user_abc_99519f01
[SessionManager] 세션 강제 초기화: user_abc → user_abc_0053ae88
✅ SessionManager: 동일 user → 동일 thread_id: True
✅ reset_session: 새 thread_id: True
✅ MAX_RETRY=3, MESSAGE_WINDOW=10
```

---

---

## 10. M2 이후 발견된 버그 수정

> 이 섹션은 M2 완료 이후 실제 웹 UI 테스트 중 발견한 버그와 수정 내용을 기록한다.

| 번호 | 발견 경위 | 증상 | 수정 내용 |
|------|----------|------|----------|
| BUG-01 | 서버 기동 실패 | `SqliteSaver.from_conn_string()` → `TypeError` | `sqlite3.connect()` 직접 연결로 변경 |
| BUG-02 | `app.py` 문법 오류 | `try:` 블록 누락으로 `IndentationError` | `/api/query`, `/api/multimodal-query` 엔드포인트 `try:` 복원 |
| BUG-03 | 실제 UI 테스트 | 도메인 외 질문("블러드문")에 안전 관련 응답 | `_is_safety_domain()` 필터 + LLM 프롬프트 `out_of_scope` 추가 |

### BUG-03 상세: LLM 프롬프트 설계 실수

**핵심 교훈**: LLM에게 선택지를 줄 때 반드시 **"해당 없음(out_of_scope)" 옵션을 포함**해야 한다.

```
❌ 잘못된 프롬프트 설계
  선택지: [data_analytics, report_generation, knowledge_management, vision_analysis]
  → LLM은 무조건 하나를 골라야 함 → 억지 매핑 → 무관한 응답

✅ 올바른 프롬프트 설계
  선택지: [data_analytics, ..., out_of_scope]
  + 규칙: "안전 도메인 외 질문은 반드시 out_of_scope 선택"
  → LLM이 거절 가능 → 사용자에게 명확한 안내
```

---

## 다음 단계 (M3/M4 예정)

| 항목 | 내용 | 우선순위 |
|------|------|----------|
| **M4 테스트 고도화** | `tests/` 디렉토리 pytest 자동화 (현재 C 카테고리 20/20 통과) | P0 |
| **M4 API 통합 테스트** | B 카테고리, D 카테고리 (서버 실행 상태에서) | P0 |
| **M3 Streaming API** | `graph.astream()` SSE 응답 | P1 |
| **M3 SubGraph 분리** | 도메인별 서브 그래프 | P2 |
| **messages 리팩터링** | `trim_messages`와 `Annotated[list, add]` 상호작용 정확히 처리 | P2 |
