const userName = document.getElementById('userName');
const userRole = document.getElementById('userRole');

// 업로드된 이미지 저장 (Base64 문자열)
let uploadedImages = [];

// 초기화
document.addEventListener('DOMContentLoaded', () => {
    console.log('페이지 로드 완료');

    // auth.js 함수 존재 여부 확인
    if (typeof isLoggedIn === 'undefined') {
        console.error('auth.js가 로드되지 않았습니다!');
        alert('인증 모듈 로드 실패. 페이지를 새로고침해주세요.');
        return;
    }

    // 로그인 확인
    if (!isLoggedIn()) {
        console.log('로그인되지 않음 - 로그인 페이지로 이동');
        window.location.href = '/static/login.html';
        return;
    }

    console.log('로그인 확인 완료');

    // 사용자 정보 표시
    displayUserInfo();

    // 이벤트 리스너 설정
    setupEventListeners();

    userInput.focus();

    console.log('초기화 완료');
});

// 사용자 정보 표시
function displayUserInfo() {
    try {
        const userInfo = getUserInfo();
        console.log('사용자 정보:', userInfo);

        if (userInfo) {
            userName.textContent = userInfo.username;

            // 역할 표시 (한글)
            const roleMap = {
                'admin': '관리자',
                'manager': '매니저',
                'viewer': '뷰어'
            };
            userRole.textContent = `(${roleMap[userInfo.role] || userInfo.role})`;
        }
    } catch (error) {
        console.error('사용자 정보 표시 오류:', error);
    }
}

// 이벤트 리스너 설정
function setupEventListeners() {
    console.log('이벤트 리스너 설정 중...');

    if (chatForm) {
        chatForm.addEventListener('submit', handleSubmit);
        console.log('폼 이벤트 리스너 등록 완료');
    } else {
        console.error('chatForm 요소를 찾을 수 없습니다!');
    }

    if (logoutBtn) {
        logoutBtn.addEventListener('click', handleLogout);
        console.log('로그아웃 버튼 이벤트 리스너 등록 완료');
    } else {
        console.error('logoutBtn 요소를 찾을 수 없습니다!');
    }

    // 이미지 업로드 리스너 설정
    const imageInput = document.getElementById('imageInput');
    const uploadDropzone = document.getElementById('uploadDropzone');

    if (uploadDropzone && imageInput) {
        // 클릭 이벤트
        uploadDropzone.addEventListener('click', () => imageInput.click());

        // 파일 선택 이벤트
        imageInput.addEventListener('change', (e) => handleFiles(e.target.files));

        // 드래그 앤 드롭 이벤트
        uploadDropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadDropzone.classList.add('drag-over');
        });

        uploadDropzone.addEventListener('dragleave', () => {
            uploadDropzone.classList.remove('drag-over');
        });

        uploadDropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadDropzone.classList.remove('drag-over');
            handleFiles(e.dataTransfer.files);
        });
    }
}

// 로그아웃 처리
function handleLogout() {
    console.log('로그아웃 시도');
    if (typeof logout === 'function') {
        logout();
    } else {
        console.error('logout 함수가 정의되지 않았습니다!');
    }
}

// 폼 제출 처리
async function handleSubmit(e) {
    e.preventDefault();
    console.log('폼 제출됨');

    const query = userInput.value.trim();

    // 텍스트와 이미지 모두 없는 경우만 무시
    if (!query && uploadedImages.length === 0) {
        console.log('빈 쿼리 및 이미지 없음 - 무시');
        return;
    }

    console.log('쿼리:', query);
    console.log('이미지 개수:', uploadedImages.length);

    // 사용자 메시지 추가 (텍스트가 있을 때만)
    if (query) {
        addMessage(query, 'user');
    }

    // 이미지가 있다면 이미지도 메시지로 표시 (선택사항, 간단히 개수만 표시하거나 미리보기 이미지를 넣을 수도 있음)
    if (uploadedImages.length > 0) {
        addMessage(`[이미지 ${uploadedImages.length}개 업로드됨]`, 'user');
    }

    // 입력 필드 초기화
    userInput.value = '';

    // 전송 버튼 비활성화
    sendBtn.disabled = true;

    // 로딩 메시지 표시
    const loadingId = addLoadingMessage();

    try {
        console.log('API 요청 시작...');

        if (typeof authenticatedFetch !== 'function') {
            throw new Error('authenticatedFetch 함수가 정의되지 않았습니다. auth.js를 확인하세요.');
        }

        let response;

        // 이미지가 있는 경우 멀티모달 쿼리로 전송
        if (uploadedImages.length > 0) {
            console.log('멀티모달 쿼리 전송');
            response = await authenticatedFetch(`${API_BASE_URL}/api/multimodal-query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    query: query || "이 이미지를 분석해주세요.", // 텍스트가 없으면 기본 쿼리 사용
                    images: uploadedImages
                })
            });

            // 전송 성공 시 이미지 목록 초기화
            if (response.ok) {
                uploadedImages = [];
                updateImagePreview();
            }

        } else {
            // 텍스트만 있는 경우 일반 쿼리로 전송
            console.log('일반 쿼리 전송');
            response = await authenticatedFetch(`${API_BASE_URL}/api/query`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ query })
            });
        }

        console.log('API 응답 상태:', response.status);

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API 요청에 실패했습니다.');
        }

        const data = await response.json();
        console.log('API 응답 데이터:', data);

        // 로딩 메시지 제거
        removeLoadingMessage(loadingId);

        // 응답 메시지 추가
        addMessage(data.response, 'assistant');

    } catch (error) {
        console.error('쿼리 처리 오류:', error);
        removeLoadingMessage(loadingId);
        addMessage(`오류: ${error.message}`, 'assistant');
    } finally {
        sendBtn.disabled = false;
        userInput.focus();
    }
}

// 메시지 추가
function addMessage(text, sender) {
    console.log(`메시지 추가 (${sender}):`, text);

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    messageDiv.innerHTML = `
        <div class="message-content">
            ${formatMessageText(text)}
        </div>
    `;

    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 메시지 텍스트 포맷팅
function formatMessageText(text) {
    // 줄바꿈을 <p> 태그로 변환
    const paragraphs = text.split('\n\n').filter(p => p.trim());
    return paragraphs.map(p => `<p>${p.replace(/\n/g, '<br>')}</p>`).join('');
}

// 로딩 메시지 추가
function addLoadingMessage() {
    const loadingId = 'loading-' + Date.now();
    const loadingDiv = document.createElement('div');
    loadingDiv.id = loadingId;
    loadingDiv.className = 'message assistant';
    loadingDiv.innerHTML = `
        <div class="loading-message">
            <span>답변 생성 중</span>
            <div class="loading-dots">
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
                <div class="loading-dot"></div>
            </div>
        </div>
    `;

    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    return loadingId;
}

// 로딩 메시지 제거
function removeLoadingMessage(loadingId) {
    const loadingElement = document.getElementById(loadingId);
    if (loadingElement) {
        loadingElement.remove();
    }
}

// --------------------------------------------------------
// 이미지 처리 관련 함수
// --------------------------------------------------------

// 파일 처리
function handleFiles(files) {
    if (!files || files.length === 0) return;

    const validFiles = Array.from(files).filter(file => {
        // 이미지 형식 확인
        if (!file.type.startsWith('image/')) {
            alert(`이미지 파일만 업로드 가능합니다: ${file.name}`);
            return false;
        }
        // 크기 확인 (10MB)
        if (file.size > 10 * 1024 * 1024) {
            alert(`파일 크기는 10MB를 초과할 수 없습니다: ${file.name}`);
            return false;
        }
        return true;
    });

    if (validFiles.length === 0) return;

    // 이미지 읽기
    validFiles.forEach(readImage);
}

// 이미지 읽기 (Base64 변환)
function readImage(file) {
    const reader = new FileReader();

    reader.onload = function (e) {
        const base64String = e.target.result;
        uploadedImages.push(base64String);
        updateImagePreview();
    };

    reader.onerror = function () {
        console.error('파일 읽기 실패:', file.name);
        alert('파일을 읽는 중 오류가 발생했습니다.');
    };

    reader.readAsDataURL(file);
}

// 이미지 미리보기 업데이트
function updateImagePreview() {
    const container = document.getElementById('imagePreviewContainer');
    if (!container) return;

    container.innerHTML = '';

    uploadedImages.forEach((imageSrc, index) => {
        const previewItem = document.createElement('div');
        previewItem.className = 'image-preview-item';

        previewItem.innerHTML = `
            <img src="${imageSrc}" alt="Preview ${index + 1}">
            <button type="button" class="image-preview-remove" onclick="removeImage(${index})">×</button>
        `;

        container.appendChild(previewItem);
    });

    // 드롭존 텍스트 업데이트 (선택사항)
    const dropzone = document.getElementById('uploadDropzone');
    if (dropzone) {
        const p = dropzone.querySelector('p');
        if (uploadedImages.length > 0) {
            p.textContent = `📎 ${uploadedImages.length}개의 이미지 선택됨 (추가하려면 클릭/드래그)`;
        } else {
            p.textContent = '📎 이미지를 드래그하거나 클릭하여 업로드';
        }
    }
}

// 이미지 삭제
window.removeImage = function (index) {
    uploadedImages.splice(index, 1);
    updateImagePreview();
};