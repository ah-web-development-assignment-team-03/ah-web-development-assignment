from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Department, Gender, Role
from app.models.user import User


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_phone_number(db: AsyncSession, phone_number: str) -> User | None:
    result = await db.execute(select(User).where(User.phone_number == phone_number))
    return result.scalar_one_or_none()


async def delete_user(db: AsyncSession, user: User) -> None:
    await db.delete(user)


async def create_user(
    db: AsyncSession,
    *,
    email: str,
    hashed_password: str,
    name: str,
    department: Department,
    gender: Gender,
    phone_number: str,
    role: Role,
) -> User:
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
    await db.refresh(user)
    return user
