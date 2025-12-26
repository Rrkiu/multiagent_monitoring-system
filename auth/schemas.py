"""
Pydantic 스키마 정의
API 요청/응답 모델
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


# 사용자 관련 스키마

class UserBase(BaseModel):
    """사용자 기본 스키마"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    """사용자 생성 스키마"""
    password: str = Field(..., min_length=6, max_length=100)
    role: Optional[str] = "viewer"  # admin, manager, viewer


class UserUpdate(BaseModel):
    """사용자 업데이트 스키마"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase):
    """사용자 응답 스키마"""
    id: int
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# 인증 관련 스키마

class LoginRequest(BaseModel):
    """로그인 요청 스키마"""
    username: str
    password: str


class TokenResponse(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 초 단위


class RefreshTokenRequest(BaseModel):
    """리프레시 토큰 요청 스키마"""
    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """비밀번호 변경 요청 스키마"""
    current_password: str
    new_password: str = Field(..., min_length=6, max_length=100)


class MessageResponse(BaseModel):
    """일반 메시지 응답 스키마"""
    message: str
    detail: Optional[str] = None
