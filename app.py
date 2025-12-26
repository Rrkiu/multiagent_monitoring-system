"""
FastAPI 백엔드 서버
Multi-Agent 시스템을 RESTful API로 제공
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import Optional
import uvicorn
from pathlib import Path
from typing import List

from agents.supervisor_agent import SupervisorAgent
from agents.security_agent import SecurityAgent
from config import settings

# 인증 시스템 import
from auth import auth_router, init_db, get_current_active_user, require_viewer
from auth.models import User

# FastAPI 앱 생성
app = FastAPI(
    title=settings.project_name,
    description="Multi-Agent 기반 안전 모니터링 시스템",
    version="1.0.0"
)

frontend_dir = Path(__file__).parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 인증 라우터 등록
app.include_router(auth_router)

# Supervisor Agent 초기화 (싱글톤)
supervisor = None
security_agent = None


def get_supervisor() -> SupervisorAgent:
    """Supervisor Agent 싱글톤 반환"""
    global supervisor
    if supervisor is None:
        print("Supervisor Agent 초기화 중...")
        supervisor = SupervisorAgent()
        print("Supervisor Agent 초기화 완료!")
    return supervisor


def get_security_agent() -> SecurityAgent:
    """Security Agent 싱글톤 반환"""
    global security_agent
    if security_agent is None:
        security_agent = SecurityAgent()
    return security_agent


# Request/Response 모델
class QueryRequest(BaseModel):
    """쿼리 요청 모델"""
    query: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    """쿼리 응답 모델"""
    response: str
    session_id: Optional[str] = None


class HealthResponse(BaseModel):
    """헬스체크 응답"""
    status: str
    message: str


class MultimodalQueryRequest(BaseModel):
    """멀티모달 쿼리 요청 모델"""
    query: str
    images: Optional[List[str]] = None  # Base64 인코딩된 이미지 또는 파일 경로
    session_id: Optional[str] = None


# API 엔드포인트

@app.get("/", response_class=HTMLResponse)
async def root():
    """루트 경로 - 프론트엔드 HTML 반환"""
    frontend_path = Path(__file__).parent / "frontend" / "index.html"

    if frontend_path.exists():
        return frontend_path.read_text(encoding='utf-8')
    else:
        return """ 
        <html>
            <body>
                <h1>Safety Monitoring Multi-Agent System</h1>
                <p>프론트엔드 파일이 없습니다. /frontend/index.html을 생성하세요.</p>
                <p>API 문서: <a href="/docs">/docs</a></p>
            </body>
        </html>
        """


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크 엔드포인트"""
    return HealthResponse(
        status="healthy",
        message="Multi-Agent 시스템이 정상 작동 중입니다."
    )


@app.post("/api/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    사용자 쿼리 처리 엔드포인트 (인증 필요)

    Args:
        request: QueryRequest (query, session_id)
        current_user: 현재 로그인한 사용자

    Returns:
        QueryResponse (response, session_id)
    """
    try:
        # 1. 보안 검사
        security = get_security_agent()
        is_safe, reason = security.check_safety(request.query)
        
        if not is_safe:
            print(f"[보안 차단] {reason}")
            return QueryResponse(
                response=f"🚫 보안 정책상 해당 요청은 처리할 수 없습니다.\n사유: {reason}",
                session_id=request.session_id
            )

        # Supervisor Agent 가져오기
        agent = get_supervisor()

        # 쿼리 처리
        response = agent.execute(request.query)

        # 응답이 비어있거나 None인 경우 처리
        if not response or response.strip() == "":
            response = "죄송합니다. 응답을 생성할 수 없습니다. 다시 시도해주세요."

        return QueryResponse(
            response=response,
            session_id=request.session_id
        )

    except StopIteration:
        return QueryResponse(
            response="응답 생성 중 오류가 발생했습니다. 질문을 다시 입력해주세요.",
            session_id=request.session_id
        )
    except Exception as e:
        import traceback
        traceback.print_exc()

        error_message = str(e)
        if "StopIteration" in error_message:
            error_message = "응답 생성 중 오류가 발생했습니다. 질문을 다시 입력해주세요."

        return QueryResponse(
            response=f"처리 중 오류가 발생했습니다: {error_message}",
            session_id=request.session_id
        )


@app.post("/api/multimodal-query", response_model=QueryResponse)
async def process_multimodal_query(
    request: MultimodalQueryRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    멀티모달 쿼리 처리 엔드포인트 (이미지 + 텍스트, 인증 필요)
    
    Args:
        request: MultimodalQueryRequest (query, images, session_id)
        current_user: 현재 로그인한 사용자
        
    Returns:
        QueryResponse (response, session_id)
    """
    try:
        # 1. 보안 검사 (이미지 쿼리도 텍스트 부분 검사)
        security = get_security_agent()
        is_safe, reason = security.check_safety(request.query)
        
        if not is_safe:
            print(f"[보안 차단] {reason}")
            return QueryResponse(
                response=f"🚫 보안 정책상 해당 요청은 처리할 수 없습니다.\n사유: {reason}",
                session_id=request.session_id
            )

        # Supervisor Agent 가져오기
        agent = get_supervisor()
        
        # 이미지가 있는 경우 MultimodalAgent로 직접 라우팅
        if request.images and len(request.images) > 0:
            print(f"\n[멀티모달 쿼리] 이미지 개수: {len(request.images)}")
            
            # 이미지 데이터 준비
            image_data = {
                "images": request.images
            }
            
            # MultimodalAgent 직접 실행
            response = agent._execute_single_agent(
                "multimodal", 
                request.query,
                image_data=image_data
            )
        else:
            # 이미지가 없으면 일반 쿼리로 처리
            response = agent.execute(request.query)
        
        # 응답이 비어있거나 None인 경우 처리
        if not response or response.strip() == "":
            response = "죄송합니다. 응답을 생성할 수 없습니다. 다시 시도해주세요."
        
        return QueryResponse(
            response=response,
            session_id=request.session_id
        )
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        error_message = str(e)
        return QueryResponse(
            response=f"멀티모달 쿼리 처리 중 오류가 발생했습니다: {error_message}",
            session_id=request.session_id
        )

@app.get("/api/agents")
async def list_agents():
    """사용 가능한 에이전트 목록 반환"""
    return {
        "agents": [
            {
                "name": "query",
                "description": "데이터 조회 전담 에이전트",
                "capabilities": [
                    "카메라별 이벤트 조회",
                    "날짜별 이벤트 조회",
                    "이벤트 타입별 조회",
                    "미해결 이벤트 조회"
                ]
            },
            {
                "name": "analysis",
                "description": "데이터 분석 전담 에이전트",
                "capabilities": [
                    "통계 계산",
                    "추세 분석",
                    "위험도 평가",
                    "문제 구역 식별"
                ]
            },
            {
                "name": "report",
                "description": "보고서 생성 전담 에이전트",
                "capabilities": [
                    "일일 보고서 작성",
                    "조치 방안 제공",
                    "안전 규정 안내",
                    "대응 가이드 생성"
                ]
            },
            {
                "name": "search",
                "description": "웹 검색 전담 에이전트",
                "capabilities": [
                    "최신 안전 규정 검색",
                    "안전 관련 뉴스 조회",
                    "기술 문서 검색",
                    "외부 정보 수집"
                ]
            },
            {
                "name": "multimodal",
                "description": "이미지 분석 전담 에이전트",
                "capabilities": [
                    "이미지 안전 위반 사항 감지",
                    "PPE(개인 보호 장비) 착용 확인",
                    "작업장 안전 상태 평가",
                    "CCTV 스냅샷 분석",
                    "이미지 기반 질의응답",
                    "개선 전후 비교 분석"
                ]
            },
            {
                "name": "supervisor",
                "description": "전체 시스템 조율 에이전트",
                "capabilities": [
                    "쿼리 라우팅",
                    "멀티스텝 작업 조율",
                    "결과 통합"
                ]
            }
        ]
    }


@app.get("/api/examples")
async def get_examples():
    """예시 쿼리 목록 반환"""
    return {
        "examples": [
            {
                "category": "데이터 조회",
                "queries": [
                    "CAM-001에서 발생한 이벤트를 보여주세요",
                    "오늘 발생한 모든 이벤트는?",
                    "안전모 미착용 이벤트가 몇 건이나 있나요?",
                    "미해결 이벤트를 보여주세요"
                ]
            },
            {
                "category": "데이터 분석",
                "queries": [
                    "2025-11-15부터 2025-11-22까지의 통계를 분석해주세요",
                    "가장 이벤트가 많은 카메라는?",
                    "최근 7일간 위험도를 평가해주세요",
                    "이번 주와 지난 주의 이벤트 증감률은?"
                ]
            },
            {
                "category": "보고서 생성",
                "queries": [
                    "오늘 발생한 이벤트 보고서를 작성해주세요",
                    "안전모 미착용에 대한 조치 방안을 알려주세요",
                    "작업자 넘어짐 사고 대응 가이드를 제공해주세요"
                ]
            },
            {
                "category": "이미지 분석",
                "queries": [
                    "이 이미지에서 안전 위반 사항을 찾아주세요",
                    "작업자들의 안전모 착용 여부를 확인해주세요",
                    "작업장의 전반적인 안전 상태를 평가해주세요",
                    "이 이미지에서 PPE 미착용자를 식별해주세요"
                ]
            },
            {
                "category": "복합 작업",
                "queries": [
                    "가장 위험한 구역의 개선 방안을 제시해주세요",
                    "이번 주 가장 많이 발생한 이벤트의 대응 방안은?",
                    "최근 일주일간 통계와 주요 조치사항을 요약해주세요"
                ]
            }
        ]
    }


@app.on_event("startup")
async def startup_event():
    """서버 시작 시 실행"""
    print("=" * 60)
    print(f"{settings.project_name} 시작")
    print("=" * 60)
    print(f"Debug Mode: {settings.debug}")
    print(f"LLM Model: {settings.llm_model}")
    print("=" * 60)

    # 데이터베이스 초기화
    print("\n데이터베이스 초기화 중...")
    init_db()

    # 에이전트 사전 초기화
    get_supervisor()
    get_security_agent()


@app.on_event("shutdown")
async def shutdown_event():
    """서버 종료 시 실행"""
    print("\n서버를 종료합니다...")


if __name__ == "__main__":
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    )


## 172.17.97.97:8000
## http://localhost:8000/static/login.html

