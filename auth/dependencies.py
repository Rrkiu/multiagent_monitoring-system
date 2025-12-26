"""
FastAPI 의존성 함수
인증 및 권한 확인
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from auth.database import get_db
from auth.auth_handler import verify_token
from auth.models import User

# HTTP Bearer 토큰 스키마
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    현재 로그인한 사용자 가져오기
    
    Args:
        credentials: HTTP Authorization 헤더의 Bearer 토큰
        db: 데이터베이스 세션
    
    Returns:
        User 객체
    
    Raises:
        HTTPException: 인증 실패 시
    """
    token = credentials.credentials
    print(f"🔍 토큰 받음: {token[:20]}..." if token else "토큰 없음")
    
    # 토큰 검증
    payload = verify_token(token, token_type="access")
    print(f"🔍 토큰 검증 결과: {payload}")
    
    if payload is None:
        print("❌ 토큰 검증 실패")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 인증 토큰입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 사용자 ID 추출 (문자열을 정수로 변환)
    user_id_str = payload.get("sub")
    print(f"🔍 사용자 ID (문자열): {user_id_str}")
    
    if user_id_str is None:
        print("❌ 사용자 ID 없음")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="토큰에서 사용자 정보를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = int(user_id_str)
        print(f"🔍 사용자 ID (정수): {user_id}")
    except (ValueError, TypeError):
        print("❌ 사용자 ID 변환 실패")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않은 사용자 ID입니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 데이터베이스에서 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    print(f"🔍 사용자 조회 결과: {user}")
    
    if user is None:
        print("❌ 사용자 없음")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="사용자를 찾을 수 없습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        print("❌ 비활성 사용자")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다.",
        )
    
    print(f"✅ 인증 성공: {user.username}")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """활성 사용자 확인"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 사용자입니다."
        )
    return current_user


def require_role(required_role: str):
    """
    특정 역할 요구 (데코레이터 팩토리)
    
    Args:
        required_role: 필요한 역할 ("admin", "manager", "viewer")
    
    Returns:
        의존성 함수
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # 역할 계층: admin > manager > viewer
        role_hierarchy = {"admin": 3, "manager": 2, "viewer": 1}
        
        user_level = role_hierarchy.get(current_user.role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"이 작업을 수행하려면 '{required_role}' 권한이 필요합니다.",
            )
        
        return current_user
    
    return role_checker


# 역할별 의존성 (편의 함수)
require_admin = require_role("admin")
require_manager = require_role("manager")
require_viewer = require_role("viewer")
