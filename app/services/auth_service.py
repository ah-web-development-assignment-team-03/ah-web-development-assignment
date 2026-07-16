from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.repositories.user_repository import get_user_by_email
from jose import JWTError


async def login(db: AsyncSession, email: str, password: str) -> tuple[str, str]:
    user = await get_user_by_email(db, email)

    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="비활성화된 계정입니다.",
        )

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return access_token, refresh_token


def reissue_access_token(refresh_token: str) -> str:
    try:
        payload = decode_token(refresh_token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="유효하지 않거나 만료된 Refresh Token입니다.",
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token이 아닙니다.",
        )

    return create_access_token(payload["user_id"])
