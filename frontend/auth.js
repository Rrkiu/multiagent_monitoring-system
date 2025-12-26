/**
 * JWT 인증 관리 모듈
 * 로그인, 로그아웃, 토큰 관리 기능 제공
 */

const API_BASE_URL = window.location.origin;

// 토큰 저장소 키
const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_INFO_KEY = 'user_info';

/**
 * 로컬 스토리지에 토큰 저장
 */
function saveTokens(accessToken, refreshToken) {
    localStorage.setItem(TOKEN_KEY, accessToken);
    localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken);
}

/**
 * 로컬 스토리지에서 액세스 토큰 가져오기
 */
function getAccessToken() {
    return localStorage.getItem(TOKEN_KEY);
}

/**
 * 로컬 스토리지에서 리프레시 토큰 가져오기
 */
function getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY);
}

/**
 * 사용자 정보 저장
 */
function saveUserInfo(userInfo) {
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo));
}

/**
 * 사용자 정보 가져오기
 */
function getUserInfo() {
    const userInfo = localStorage.getItem(USER_INFO_KEY);
    return userInfo ? JSON.parse(userInfo) : null;
}

/**
 * 모든 인증 정보 삭제
 */
function clearAuth() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_INFO_KEY);
}

/**
 * 로그인 여부 확인
 */
function isLoggedIn() {
    return !!getAccessToken();
}

/**
 * 로그인 처리
 */
async function login(username, password) {
    try {
        console.log('로그인 시도:', username);

        const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ username, password })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || '로그인에 실패했습니다.');
        }

        const data = await response.json();
        console.log('로그인 응답:', {
            access_token: data.access_token ? data.access_token.substring(0, 20) + '...' : 'null',
            refresh_token: data.refresh_token ? 'exists' : 'null'
        });

        // 토큰 저장
        saveTokens(data.access_token, data.refresh_token);
        console.log('토큰 저장 완료');

        // 저장 확인
        const savedToken = getAccessToken();
        console.log('저장된 토큰 확인:', savedToken ? savedToken.substring(0, 20) + '...' : 'null');

        // 사용자 정보 가져오기
        await fetchUserInfo();

        return { success: true };
    } catch (error) {
        console.error('로그인 오류:', error);
        return { success: false, error: error.message };
    }
}

/**
 * 현재 사용자 정보 가져오기
 */
async function fetchUserInfo() {
    try {
        const token = getAccessToken();
        console.log('fetchUserInfo - 토큰:', token ? token.substring(0, 20) + '...' : 'null');

        const response = await fetch(`${API_BASE_URL}/api/auth/me`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        console.log('fetchUserInfo - 응답 상태:', response.status);

        if (!response.ok) {
            const errorData = await response.json();
            console.error('fetchUserInfo - 에러:', errorData);
            throw new Error('사용자 정보를 가져올 수 없습니다.');
        }

        const userInfo = await response.json();
        console.log('fetchUserInfo - 사용자 정보:', userInfo);
        saveUserInfo(userInfo);
        return userInfo;
    } catch (error) {
        console.error('Failed to fetch user info:', error);
        return null;
    }
}

/**
 * 토큰 갱신
 */
async function refreshAccessToken() {
    try {
        const refreshToken = getRefreshToken();
        if (!refreshToken) {
            throw new Error('리프레시 토큰이 없습니다.');
        }

        const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh_token: refreshToken })
        });

        if (!response.ok) {
            throw new Error('토큰 갱신에 실패했습니다.');
        }

        const data = await response.json();
        saveTokens(data.access_token, data.refresh_token);

        return { success: true };
    } catch (error) {
        clearAuth();
        return { success: false, error: error.message };
    }
}

/**
 * 로그아웃 처리
 */
async function logout() {
    try {
        const refreshToken = getRefreshToken();
        const accessToken = getAccessToken();

        if (refreshToken && accessToken) {
            await fetch(`${API_BASE_URL}/api/auth/logout`, {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${accessToken}`,
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ refresh_token: refreshToken })
            });
        }
    } catch (error) {
        console.error('Logout error:', error);
    } finally {
        clearAuth();
        window.location.href = '/static/login.html';
    }
}

/**
 * 인증이 필요한 API 요청
 */
async function authenticatedFetch(url, options = {}) {
    const accessToken = getAccessToken();

    if (!accessToken) {
        window.location.href = '/static/login.html';
        throw new Error('인증이 필요합니다.');
    }

    // Authorization 헤더 추가
    const headers = {
        ...options.headers,
        'Authorization': `Bearer ${accessToken}`
    };

    let response = await fetch(url, { ...options, headers });

    // 401 에러 시 토큰 갱신 시도
    if (response.status === 401) {
        const refreshResult = await refreshAccessToken();

        if (refreshResult.success) {
            // 갱신된 토큰으로 재시도
            headers.Authorization = `Bearer ${getAccessToken()}`;
            response = await fetch(url, { ...options, headers });
        } else {
            // 갱신 실패 시 로그인 페이지로 이동
            window.location.href = '/static/login.html';
            throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
        }
    }

    return response;
}

// 로그인 페이지 로직
if (window.location.pathname.includes('login.html')) {
    document.addEventListener('DOMContentLoaded', () => {
        // 이미 로그인되어 있으면 메인 페이지로 이동
        if (isLoggedIn()) {
            window.location.href = '/';
            return;
        }

        const loginForm = document.getElementById('loginForm');
        const loginBtn = document.getElementById('loginBtn');
        const errorMessage = document.getElementById('errorMessage');

        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;

            // 에러 메시지 숨기기
            errorMessage.classList.remove('show');

            // 버튼 비활성화
            loginBtn.disabled = true;
            loginBtn.textContent = '로그인 중...';

            // 로그인 시도
            const result = await login(username, password);

            if (result.success) {
                // 로그인 성공 - 메인 페이지로 이동
                window.location.href = '/';
            } else {
                // 로그인 실패 - 에러 메시지 표시
                errorMessage.textContent = result.error;
                errorMessage.classList.add('show');

                loginBtn.disabled = false;
                loginBtn.textContent = '로그인';
            }
        });
    });
}
