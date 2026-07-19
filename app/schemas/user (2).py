# app/services/user.py
"""User 비즈니스 로직 계층.

REQ-USER-001 회원가입 규칙:
1. 이메일 중복 금지 -> 409
2. 휴대폰 번호 중복 금지 -> 409
3. 비밀번호는 해싱 후 저장 (NFR-USER-002 백엔드 대응)
4. 가입 직후 권한은 PENDING 자동 부여
"""
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.enums import Role
from app.models.user import User
from app.repositories import user as user_repo
from app.schemas.user import UserCreate


async def register_user(db: AsyncSession, user_data: UserCreate) -> User:
    """회원가입 처리. 성공 시 생성된 User를 반환한다."""
    # 규칙 1: 이메일 중복 검사
    if await user_repo.get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 이메일입니다.",
        )

    # 규칙 2: 휴대폰 번호 중복 검사
    if await user_repo.get_user_by_phone_number(db, user_data.phone_number):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="이미 사용 중인 휴대폰 번호입니다.",
        )

    # 규칙 3: 비밀번호 해싱 (평문은 저장하지 않는다)
    hashed = hash_password(user_data.password)

    # 규칙 4: 권한 PENDING 자동 부여 후 저장
    return await user_repo.create_user(
        db,
        email=user_data.email,
        hashed_password=hashed,
        name=user_data.name,
        department=user_data.department,
        gender=user_data.gender,
        phone_number=user_data.phone_number,
        role=Role.PENDING,
    )
