from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.models.enums import Department, Gender, Role
from app.models.user import User


router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])


class UserListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    department: Department
    gender: Gender
    phone_number: str
    is_active: bool


class UserListResponse(BaseModel):
    items: list[UserListItem]
    page: int
    size: int
    total: int


class UserRoleUpdate(BaseModel):
    role: Role


class UserRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    role: Role


@router.get(
    "",
    summary="관리자 회원 목록 조회",
    response_model=UserListResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "인증이 필요합니다."},
        403: {"description": "관리자 권한이 필요합니다."},
    },
)
async def get_admin_users(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=255,
            description="이메일 또는 이름 검색어",
        ),
    ] = None,
    department: Annotated[
        Department | None,
        Query(description="부서 필터"),
    ] = None,
    page: Annotated[
        int,
        Query(ge=1, description="조회할 페이지 번호"),
    ] = 1,
    size: Annotated[
        int,
        Query(ge=1, le=100, description="페이지당 회원 수"),
    ] = 20,
) -> UserListResponse:
    """관리자가 회원 목록을 검색, 필터 및 페이지 단위로 조회합니다."""

    # TODO: 인증 담당자의 공통 의존성이 병합되면
    # 현재 로그인 사용자 확인과 ADMIN 권한 검사를 추가합니다.
    conditions = []

    if search is not None:
        search_pattern = f"%{search.strip()}%"
        conditions.append(
            or_(
                User.email.ilike(search_pattern),
                User.name.ilike(search_pattern),
            )
        )

    if department is not None:
        conditions.append(User.department == department)

    count_query = select(func.count(User.id))
    users_query = select(User)

    if conditions:
        count_query = count_query.where(*conditions)
        users_query = users_query.where(*conditions)

    total = (await db.execute(count_query)).scalar_one()

    users_query = (
        users_query.order_by(User.id)
        .offset((page - 1) * size)
        .limit(size)
    )
    users = (await db.execute(users_query)).scalars().all()

    return UserListResponse(
        items=[UserListItem.model_validate(user) for user in users],
        page=page,
        size=size,
        total=total,
    )


@router.patch(
    "/{user_id}/role",
    summary="관리자 회원 권한 변경",
    response_model=UserRoleResponse,
    status_code=status.HTTP_200_OK,
    responses={
        401: {"description": "인증이 필요합니다."},
        403: {"description": "관리자 권한이 필요합니다."},
        404: {"description": "회원을 찾을 수 없습니다."},
    },
)
async def update_user_role(
    user_id: Annotated[int, Path(ge=1, description="권한을 변경할 회원 ID")],
    payload: UserRoleUpdate,
    db: Annotated[AsyncSession, Depends(async_get_db)],
) -> UserRoleResponse:
    """관리자가 특정 회원의 권한을 변경합니다."""

    # TODO: 인증 담당자의 공통 의존성이 병합되면
    # 현재 로그인 사용자 확인과 ADMIN 권한 검사를 추가합니다.
    user = await db.get(User, user_id)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="회원을 찾을 수 없습니다.",
        )

    user.role = payload.role
    await db.commit()
    await db.refresh(user)

    return UserRoleResponse.model_validate(user)
