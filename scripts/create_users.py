"""
초기 관리자 계정 생성 스크립트
데이터베이스에 기본 사용자 계정을 생성합니다.
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from auth.database import SessionLocal, init_db
from auth.models import User
from auth.auth_handler import get_password_hash


def create_default_users():
    """기본 사용자 계정 생성"""
    
    # 데이터베이스 초기화
    print("데이터베이스 초기화 중...")
    init_db()
    
    db = SessionLocal()
    
    try:
        # 기본 사용자 데이터
        default_users = [
            {
                "username": "admin",
                "email": "admin@safety.com",
                "password": "admin123",
                "full_name": "시스템 관리자",
                "role": "admin"
            },
            {
                "username": "manager",
                "email": "manager@safety.com",
                "password": "manager123",
                "full_name": "안전 관리자",
                "role": "manager"
            },
            {
                "username": "viewer",
                "email": "viewer@safety.com",
                "password": "viewer123",
                "full_name": "일반 사용자",
                "role": "viewer"
            }
        ]
        
        print("\n기본 사용자 계정 생성 중...\n")
        
        for user_data in default_users:
            # 이미 존재하는지 확인
            existing_user = db.query(User).filter(
                User.username == user_data["username"]
            ).first()
            
            if existing_user:
                print(f"⚠️  사용자 '{user_data['username']}'는 이미 존재합니다. 건너뜁니다.")
                continue
            
            # 새 사용자 생성
            new_user = User(
                username=user_data["username"],
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                full_name=user_data["full_name"],
                role=user_data["role"],
                is_active=True
            )
            
            db.add(new_user)
            db.commit()
            
            print(f"✅ 사용자 생성 완료:")
            print(f"   - 사용자명: {user_data['username']}")
            print(f"   - 이메일: {user_data['email']}")
            print(f"   - 역할: {user_data['role']}")
            print(f"   - 비밀번호: {user_data['password']}")
            print()
        
        print("=" * 60)
        print("기본 사용자 계정 생성이 완료되었습니다!")
        print("=" * 60)
        print("\n⚠️  보안 경고: 프로덕션 환경에서는 반드시 비밀번호를 변경하세요!\n")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    create_default_users()
