from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_password
from app.models.user import User
from app.repositories.user_repository import get_user_by_phone_number
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
    """REQ-USER-008. 기존 비밀번호가 저장된 해시와 일치하는지 검증한다.

    불일치 시 403으로 응답한다. (명세 비고: 400/401은 프런트엔드 동작상 사용 불가)

    새 비밀번호 정책 검증(400)과 해싱은 REQ-USER-001 담당자의 공용 모듈이
    develop에 병합되면 연결한다. 이 함수는 그 전까지 독립적으로 사용·검증 가능한
    기존 비밀번호 확인 로직만 담당한다.
    """
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="기존 비밀번호가 일치하지 않습니다.",
        )
