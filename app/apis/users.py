from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_cookie import delete_refresh_token_cookie
from app.core.db.databases import async_get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import (
    MessageResponse,
    MyInfoUpdateRequest,
    MyPageResponse,
    PasswordChangeRequest,
    UserDeleteRequest,
)
from app.services.user_service import (
    change_my_password,
    delete_current_user,
    update_my_info,
)


router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/me", response_model=MyPageResponse)
async def get_my_info_handler(
    current_user: User = Depends(get_current_user),
) -> MyPageResponse:
    """REQ-USER-006. 로그인 사용자 본인의 정보를 조회한다. (pending 사용자도 접근 가능)"""
    return MyPageResponse.from_user(current_user)


@router.patch("/me", response_model=MyPageResponse)
async def update_my_info_handler(
    request: MyInfoUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
) -> MyPageResponse:
    """REQ-USER-007. 본인의 부서·휴대폰 번호를 Partial로 수정한다."""
    updated_user = await update_my_info(db, current_user, request)
    return MyPageResponse.from_user(updated_user)


@router.patch("/me/password", response_model=MessageResponse)
async def change_my_password_handler(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
) -> MessageResponse:
    """REQ-USER-008. 기존 비밀번호 확인 후 새 비밀번호로 변경한다."""
    await change_my_password(
        db, current_user, request.current_password, request.new_password
    )
    return MessageResponse(detail="비밀번호가 변경되었습니다.")


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_current_user_handler(
    request: UserDeleteRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(async_get_db),
) -> Response:
    await delete_current_user(db, current_user, request.current_password)
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    delete_refresh_token_cookie(response)
    return response
