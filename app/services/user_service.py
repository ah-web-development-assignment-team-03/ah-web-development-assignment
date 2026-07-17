from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import delete_user


async def delete_current_user(
    db: AsyncSession,
    current_user: User,
    current_password: str,
) -> None:
    """현재 비밀번호를 확인한 뒤 로그인 사용자를 하드 삭제한다."""
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="현재 비밀번호가 일치하지 않습니다.",
        )

    try:
        await delete_user(db, current_user)
        await db.commit()
    except SQLAlchemyError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원 탈퇴 처리 중 오류가 발생했습니다.",
        ) from exc
