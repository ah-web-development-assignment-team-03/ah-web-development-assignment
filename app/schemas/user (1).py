# app/apis/user.py
"""User API Router.

명세서 기준: POST /api/users (회원가입, REQ-USER-001)
Router는 얇게 유지한다: 요청 수신 -> Service 호출 -> 응답 반환.
"""
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.schemas.user import UserCreate, UserResponse
from app.services import user as user_service

router = APIRouter(prefix="/api/users", tags=["users"])


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    description="사내 의료인, 개발 실무진, 연구진이 회원가입을 통해 서비스를 이용할 수 있다. (REQ-USER-001)",
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(async_get_db),
) -> UserResponse:
    user = await user_service.register_user(db, user_data)
    return user
