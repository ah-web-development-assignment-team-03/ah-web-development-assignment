from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_cookie import delete_refresh_token_cookie
from app.core.db.databases import async_get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.user import UserDeleteRequest
from app.services.user_service import delete_current_user


router = APIRouter(prefix="/api/v1/users", tags=["users"])


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
