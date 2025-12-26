# JWT 인증 시스템 가이드

## 📋 개요

Safety Monitoring Multi-Agent System에 JWT 기반 인증 시스템이 추가되었습니다.

### 주요 기능
- ✅ JWT 기반 Access Token & Refresh Token
- ✅ 역할 기반 접근 제어 (RBAC): Admin, Manager, Viewer
- ✅ 비밀번호 해싱 (bcrypt)
- ✅ 토큰 갱신 및 로그아웃
- ✅ 사용자 관리 (생성, 조회, 수정)

---

## 🚀 시작하기

### 1. 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 변수 설정 (.env)

`.env` 파일에 다음 설정을 추가하세요:

```env
# 기존 설정
GOOGLE_API_KEY=your_google_api_key

# JWT 인증 설정 (선택사항 - 기본값 사용 가능)
SECRET_KEY=your-secret-key-change-this-in-production-min-32-chars
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DATABASE_URL=sqlite:///./data/safety_auth.db
```

⚠️ **중요**: 프로덕션 환경에서는 반드시 `SECRET_KEY`를 변경하세요!

### 3. 데이터베이스 초기화 및 기본 사용자 생성

```bash
python scripts/create_users.py
```

이 스크립트는 다음 기본 계정을 생성합니다:

| 사용자명 | 비밀번호 | 역할 | 설명 |
|---------|---------|------|------|
| admin | admin123 | admin | 시스템 관리자 |
| manager | manager123 | manager | 안전 관리자 |
| viewer | viewer123 | viewer | 일반 사용자 |

### 4. 서버 실행

```bash
python app.py
```

서버가 `http://localhost:8000`에서 실행됩니다.

---

## 📚 API 사용법

### 인증 API

#### 1. 회원가입
```http
POST /api/auth/register
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "password123",
  "full_name": "홍길동",
  "role": "viewer"
}
```

#### 2. 로그인
```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**응답:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

#### 3. 현재 사용자 정보 조회
```http
GET /api/auth/me
Authorization: Bearer {access_token}
```

#### 4. 토큰 갱신
```http
POST /api/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 5. 로그아웃
```http
POST /api/auth/logout
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 6. 비밀번호 변경
```http
POST /api/auth/change-password
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "current_password": "oldpassword",
  "new_password": "newpassword123"
}
```

### 보호된 API 사용

기존 API 엔드포인트는 이제 인증이 필요합니다:

```http
POST /api/query
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "query": "오늘 발생한 이벤트를 보여주세요"
}
```

---

## 🔐 역할 및 권한

### 역할 계층
- **Admin** (최고 권한)
  - 모든 기능 접근 가능
  - 사용자 관리
  - 시스템 설정 변경

- **Manager** (중간 권한)
  - 데이터 조회 및 분석
  - 보고서 생성
  - 일부 관리 기능

- **Viewer** (기본 권한)
  - 데이터 조회
  - 기본 쿼리 실행

### 권한 확인 예시

```python
from fastapi import Depends
from auth import require_admin, require_manager, require_viewer

# Admin만 접근 가능
@app.post("/api/admin/users")
async def create_user(current_user = Depends(require_admin)):
    ...

# Manager 이상 접근 가능
@app.get("/api/reports")
async def get_reports(current_user = Depends(require_manager)):
    ...

# Viewer 이상 (모든 사용자) 접근 가능
@app.get("/api/data")
async def get_data(current_user = Depends(require_viewer)):
    ...
```

---

## 🧪 테스트

### 자동 테스트 실행

```bash
python scripts/test_auth.py
```

이 스크립트는 다음을 테스트합니다:
- ✅ 로그인
- ✅ 사용자 정보 조회
- ✅ 인증된 API 호출
- ✅ 인증 없는 API 호출 (실패 확인)
- ✅ 토큰 갱신
- ✅ 로그아웃

### 수동 테스트 (curl)

```bash
# 1. 로그인
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 2. 토큰을 변수에 저장
TOKEN="your_access_token_here"

# 3. 인증된 요청
curl -X POST http://localhost:8000/api/query \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"오늘 발생한 이벤트를 보여주세요"}'
```

---

## 📂 프로젝트 구조

```
safety_multiagent/
├── auth/                          # 인증 모듈
│   ├── __init__.py               # 패키지 초기화
│   ├── models.py                 # 데이터베이스 모델 (User, RefreshToken)
│   ├── database.py               # DB 연결 및 세션 관리
│   ├── auth_handler.py           # JWT 토큰 생성/검증
│   ├── schemas.py                # Pydantic 스키마
│   ├── dependencies.py           # FastAPI 의존성 (권한 체크)
│   └── routes.py                 # 인증 API 엔드포인트
├── scripts/
│   ├── create_users.py           # 초기 사용자 생성
│   └── test_auth.py              # 인증 테스트
├── data/
│   └── safety_auth.db            # SQLite 데이터베이스 (자동 생성)
├── app.py                        # FastAPI 메인 앱 (인증 통합)
├── config/settings.py            # 설정 (JWT 설정 추가)
└── requirements.txt              # 패키지 목록 (인증 패키지 추가)
```

---

## 🔧 설정 옵션

`config/settings.py`에서 다음 설정을 변경할 수 있습니다:

```python
# JWT 인증 설정
secret_key: str = "your-secret-key"           # JWT 서명 키
algorithm: str = "HS256"                       # 암호화 알고리즘
access_token_expire_minutes: int = 30          # Access Token 만료 시간 (분)
refresh_token_expire_days: int = 7             # Refresh Token 만료 시간 (일)

# 데이터베이스 설정
database_url: str = "sqlite:///./data/safety_auth.db"  # DB 경로
```

---

## 🛡️ 보안 권장사항

1. **SECRET_KEY 변경**
   - 프로덕션 환경에서는 반드시 강력한 시크릿 키 사용
   - 최소 32자 이상의 랜덤 문자열 권장

2. **HTTPS 사용**
   - 프로덕션에서는 HTTPS를 통해 토큰 전송

3. **비밀번호 정책**
   - 최소 6자 이상 (필요시 더 강화)
   - 정기적인 비밀번호 변경 권장

4. **토큰 만료 시간**
   - Access Token: 짧게 (15-30분)
   - Refresh Token: 길게 (7-30일)

5. **CORS 설정**
   - 프로덕션에서는 `allow_origins`를 특정 도메인으로 제한

---

## 📖 API 문서

서버 실행 후 다음 URL에서 자동 생성된 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## ❓ FAQ

### Q: 토큰이 만료되면 어떻게 하나요?
A: Refresh Token을 사용하여 새로운 Access Token을 발급받으세요.

### Q: 비밀번호를 잊어버렸어요.
A: 현재는 관리자가 데이터베이스에서 직접 재설정해야 합니다. 향후 비밀번호 재설정 기능 추가 예정입니다.

### Q: 사용자 역할을 변경하려면?
A: 관리자 권한으로 사용자 업데이트 API를 사용하거나, 데이터베이스에서 직접 수정할 수 있습니다.

### Q: 데이터베이스를 PostgreSQL로 변경하려면?
A: `config/settings.py`의 `database_url`을 PostgreSQL 연결 문자열로 변경하세요:
```python
database_url = "postgresql://user:password@localhost/dbname"
```

---

## 🔄 업데이트 내역

### v1.0.0 (2025-12-11)
- ✅ JWT 기반 인증 시스템 추가
- ✅ 역할 기반 접근 제어 (RBAC)
- ✅ 사용자 관리 기능
- ✅ 토큰 갱신 및 로그아웃
- ✅ 기존 API에 인증 적용

---

## 📞 지원

문제가 발생하거나 질문이 있으시면 이슈를 등록해주세요.
