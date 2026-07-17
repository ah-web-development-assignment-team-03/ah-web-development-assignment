# app/repositories/user.py
"""User 테이블 DB 접근 계층 (CRUD).

HTTP나 비즈니스 규칙을 다루지 않고 DB 작업에만 집중한다.
"""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Role
from app.models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """이메일로 유저 조회. 없으면 None. (중복 검사용)"""
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_phone_number(db: AsyncSession, phone_number: str) -> User | None:
    """휴대폰 번호로 유저 조회. 없으면 None. (중복 검사용)"""
    result = await db.execute(select(User).where(User.phone_number == phone_number))
    return result.scalar_one_or_none()


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    hashed_password: str,
    name: str,
    department,
    gender,
    phone_number: str,
    role: Role,
) -> User:
    """유저를 생성하고 커밋한다."""
    user = User(
        email=email,
        hashed_password=hashed_password,
        name=name,
        department=department,
        gender=gender,
        phone_number=phone_number,
        role=role,
        is_active=True,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)  # DB가 생성한 id, created_at 등을 다시 읽어옴
    return user
