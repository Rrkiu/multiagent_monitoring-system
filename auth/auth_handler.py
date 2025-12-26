"""
JWT 토큰 생성 및 검증 핸들러
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import bcrypt
from config.settings import settings


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    비밀번호 검증
    
    Args:
        plain_password: 평문 비밀번호
        hashed_password: 해시된 비밀번호
    
    Returns:
        bool: 비밀번호 일치 여부
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str) -> str:
    """
    비밀번호 해싱
    
    Args:
        password: 평문 비밀번호
    
    Returns:
        str: 해시된 비밀번호
    """
    # bcrypt는 최대 72바이트까지만 지원
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Access Token 생성
    
    Args:
        data: 토큰에 포함할 데이터 (user_id, username, role 등)
        expires_delta: 만료 시간 (기본값: 30분)
    
    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    
    to_encode.update({
        "exp": expire,
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Refresh Token 생성
    
    Args:
        data: 토큰에 포함할 데이터 (user_id)
        expires_delta: 만료 시간 (기본값: 7일)
    
    Returns:
        JWT 토큰 문자열
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    
    to_encode.update({
        "exp": expire,
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    JWT 토큰 디코딩 및 검증
    
    Args:
        token: JWT 토큰 문자열
    
    Returns:
        디코딩된 페이로드 또는 None
    """
    try:
        print(f"🔐 토큰 디코딩 시도...")
        print(f"🔐 SECRET_KEY: {settings.secret_key[:20]}...")
        print(f"🔐 ALGORITHM: {settings.algorithm}")
        
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        print(f"✅ 토큰 디코딩 성공: {payload}")
        return payload
    except JWTError as e:
        print(f"❌ JWT 디코딩 실패: {type(e).__name__}: {str(e)}")
        return None
    except Exception as e:
        print(f"❌ 예상치 못한 오류: {type(e).__name__}: {str(e)}")
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    토큰 검증 및 타입 확인
    
    Args:
        token: JWT 토큰
        token_type: 토큰 타입 ("access" 또는 "refresh")
    
    Returns:
        검증된 페이로드 또는 None
    """
    print(f"🔍 verify_token 호출 - token_type: {token_type}")
    payload = decode_token(token)
    
    if payload is None:
        print("❌ payload가 None")
        return None
    
    # 토큰 타입 확인
    actual_type = payload.get("type")
    print(f"🔍 토큰 타입 확인 - 예상: {token_type}, 실제: {actual_type}")
    
    if actual_type != token_type:
        print(f"❌ 토큰 타입 불일치")
        return None
    
    print(f"✅ 토큰 검증 완료")
    return payload
