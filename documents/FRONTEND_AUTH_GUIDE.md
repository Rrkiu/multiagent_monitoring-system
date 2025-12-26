# 🔐 프론트엔드 JWT 인증 가이드

## 📋 개요

프론트엔드에 JWT 기반 인증 시스템이 추가되었습니다. 이제 사용자는 로그인 후에만 시스템을 사용할 수 있습니다.

---

## 🎯 인증 플로우

### 1. 사용자가 처음 접속할 때

```
사용자 → http://localhost:8000/
       ↓
   로그인 확인 (auth.js)
       ↓
   토큰 없음 → /static/login.html로 리다이렉트
```

### 2. 로그인 과정

```
사용자 → 로그인 페이지 (/static/login.html)
       ↓
   사용자명/비밀번호 입력
       ↓
   POST /api/auth/login
       ↓
   Access Token + Refresh Token 받기
       ↓
   로컬 스토리지에 저장
       ↓
   사용자 정보 가져오기 (GET /api/auth/me)
       ↓
   메인 페이지(/)로 리다이렉트
```

### 3. 인증된 API 요청

```
사용자 → 쿼리 입력
       ↓
   POST /api/query
   Header: Authorization: Bearer {access_token}
       ↓
   응답 받기
```

### 4. 토큰 만료 시

```
API 요청 → 401 Unauthorized
         ↓
   Refresh Token으로 갱신 시도
         ↓
   성공 → 새 토큰으로 재시도
   실패 → 로그인 페이지로 리다이렉트
```

### 5. 로그아웃

```
사용자 → 로그아웃 버튼 클릭
       ↓
   POST /api/auth/logout
       ↓
   로컬 스토리지 토큰 삭제
       ↓
   로그인 페이지로 리다이렉트
```

---

## 📁 파일 구조

```
frontend/
├── login.html          # 로그인 페이지
├── index.html          # 메인 페이지 (인증 필요)
├── auth.js             # 인증 관리 모듈
├── script.js           # 메인 로직 (인증 통합)
└── style.css           # 스타일 (사용자 정보 UI 포함)
```

---

## 🔑 주요 함수 (auth.js)

### 토큰 관리

```javascript
// 토큰 저장
saveTokens(accessToken, refreshToken)

// 토큰 가져오기
getAccessToken()
getRefreshToken()

// 로그인 여부 확인
isLoggedIn()

// 모든 인증 정보 삭제
clearAuth()
```

### 인증 처리

```javascript
// 로그인
const result = await login(username, password);
if (result.success) {
    // 로그인 성공
} else {
    // 실패: result.error
}

// 로그아웃
await logout();

// 토큰 갱신
const result = await refreshAccessToken();

// 사용자 정보 가져오기
const userInfo = await fetchUserInfo();
```

### 인증된 API 요청

```javascript
// 자동으로 Authorization 헤더 추가 및 토큰 갱신 처리
const response = await authenticatedFetch('/api/query', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({ query: '...' })
});
```

---

## 💾 로컬 스토리지 구조

```javascript
localStorage = {
    'access_token': 'eyJhbGc...',      // Access Token (30분 유효)
    'refresh_token': 'eyJhbGc...',     // Refresh Token (7일 유효)
    'user_info': '{                     // 사용자 정보 (JSON)
        "id": 1,
        "username": "admin",
        "email": "admin@safety.com",
        "role": "admin",
        "is_active": true,
        "created_at": "2025-12-11T..."
    }'
}
```

---

## 🎨 UI 컴포넌트

### 로그인 페이지 (login.html)

- **사용자명 입력**
- **비밀번호 입력**
- **로그인 버튼**
- **에러 메시지 표시**
- **테스트 계정 안내**

### 메인 페이지 (index.html)

- **헤더**
  - 시스템 제목
  - 사용자 정보 (이름, 역할)
  - 로그아웃 버튼

- **챗 영역**
  - 메시지 표시
  - 입력 폼

---

## 🔒 보안 기능

### 1. 자동 로그인 확인

```javascript
// script.js에서 페이지 로드 시 실행
document.addEventListener('DOMContentLoaded', () => {
    if (!isLoggedIn()) {
        window.location.href = '/static/login.html';
        return;
    }
    // ...
});
```

### 2. 자동 토큰 갱신

```javascript
// authenticatedFetch 함수에서 자동 처리
if (response.status === 401) {
    const refreshResult = await refreshAccessToken();
    if (refreshResult.success) {
        // 갱신된 토큰으로 재시도
    } else {
        // 로그인 페이지로 이동
    }
}
```

### 3. 안전한 로그아웃

```javascript
// 서버에 로그아웃 요청 + 로컬 스토리지 삭제
async function logout() {
    try {
        await fetch('/api/auth/logout', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAccessToken()}`,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: getRefreshToken() })
        });
    } finally {
        clearAuth();
        window.location.href = '/static/login.html';
    }
}
```

---

## 🧪 테스트 방법

### 1. 서버 실행

```bash
python app.py
```

### 2. 브라우저에서 접속

```
http://localhost:8000/
```

### 3. 로그인 테스트

**테스트 계정:**
- **관리자**: `admin` / `admin123`
- **매니저**: `manager` / `manager123`
- **뷰어**: `viewer` / `viewer123`

### 4. 기능 테스트

1. ✅ 로그인 성공 → 메인 페이지로 이동
2. ✅ 사용자 정보 표시 (헤더에 이름, 역할)
3. ✅ 쿼리 전송 → 인증된 API 호출
4. ✅ 로그아웃 → 로그인 페이지로 이동
5. ✅ 로그아웃 후 메인 페이지 접근 → 로그인 페이지로 리다이렉트

### 5. 개발자 도구로 확인

**F12 → Application → Local Storage**
- `access_token` 확인
- `refresh_token` 확인
- `user_info` 확인

**F12 → Network**
- API 요청 헤더에 `Authorization: Bearer ...` 확인

---

## 🐛 문제 해결

### Q: 로그인 후 계속 로그인 페이지로 돌아갑니다.

**A:** 브라우저 콘솔(F12)에서 에러 확인
- 토큰이 제대로 저장되었는지 확인
- API 응답이 정상인지 확인

### Q: "인증이 필요합니다" 에러가 나옵니다.

**A:** 토큰이 만료되었거나 없습니다.
- 로그아웃 후 다시 로그인
- 로컬 스토리지 확인

### Q: 토큰 갱신이 작동하지 않습니다.

**A:** Refresh Token이 만료되었을 수 있습니다.
- Refresh Token은 7일 유효
- 다시 로그인 필요

### Q: CORS 에러가 발생합니다.

**A:** 서버 설정 확인
- `app.py`에서 CORS 설정 확인
- 브라우저와 서버가 같은 origin인지 확인

---

## 📝 커스터마이징

### 토큰 만료 시간 변경

`config/settings.py`:
```python
access_token_expire_minutes: int = 30  # 30분 → 원하는 시간
refresh_token_expire_days: int = 7     # 7일 → 원하는 일수
```

### 로그인 페이지 디자인 변경

`frontend/login.html` 및 인라인 스타일 수정

### 사용자 정보 표시 커스터마이징

`frontend/script.js`의 `displayUserInfo()` 함수 수정:
```javascript
function displayUserInfo() {
    const userInfo = getUserInfo();
    if (userInfo) {
        userName.textContent = userInfo.username;
        // 원하는 정보 추가
    }
}
```

---

## 🔄 향후 개선 사항

- [ ] "Remember Me" 기능
- [ ] 비밀번호 재설정
- [ ] 회원가입 페이지
- [ ] 프로필 수정 페이지
- [ ] 세션 타임아웃 경고
- [ ] 다중 탭 동기화

---

## 📞 지원

문제가 발생하면 브라우저 콘솔(F12)에서 에러 메시지를 확인하고,
서버 로그도 함께 확인하세요.
