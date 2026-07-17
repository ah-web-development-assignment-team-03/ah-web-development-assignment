from fastapi import HTTPException, status
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import delete_user, get_user_by_phone_number
from app.schemas.user import DEPARTMENT_API_TO_DB, MyInfoUpdateRequest


async def update_my_info(
    db: AsyncSession,
    current_user: User,
    payload: MyInfoUpdateRequest,
) -> User:
    """REQ-USER-007. 부서·휴대폰 번호를 Partial로 수정한다.

    - 요청에 전달된 필드만 변경하고, 전달되지 않은 필드는 그대로 유지한다.
    - 휴대폰 번호는 자기 자신을 제외하고 중복을 검사한다(중복 시 409).
    - 부서는 프런트엔드 값 → DB Enum으로 변환해 저장한다.
    """
    fields_set = payload.model_fields_set

    if "phone_number" in fields_set and payload.phone_number is not None:
        existing = await get_user_by_phone_number(db, payload.phone_number)
        if existing is not None and existing.id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="이미 사용 중인 휴대폰 번호입니다.",
            )
        current_user.phone_number = payload.phone_number

    if "department" in fields_set and payload.department is not None:
        current_user.department = DEPARTMENT_API_TO_DB[payload.department]

    await db.commit()
    await db.refresh(current_user)
    return current_user


def verify_current_password(current_user: User, current_password: str) -> None:
    """기존 비밀번호가 저장된 해시와 일치하는지 검증한다.

    불일치 시 403으로 응답한다. (명세 비고: 400/401은 프런트엔드 동작상 사용 불가)
    """
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="기존 비밀번호가 일치하지 않습니다.",
        )


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
