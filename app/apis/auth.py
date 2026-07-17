from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth_cookie import (
    REFRESH_TOKEN_COOKIE,
    delete_refresh_token_cookie,
    set_refresh_token_cookie,
)
from app.core.db.databases import async_get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import login, reissue_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse, status_code=200)
async def login_handler(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(async_get_db),
):
    access_token, refresh_token = await login(db, request.email, request.password)

    set_refresh_token_cookie(response, refresh_token)

    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse, status_code=200)
async def refresh_handler(
    refresh_token: str | None = Cookie(default=None, alias=REFRESH_TOKEN_COOKIE),
):
    if refresh_token is None:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh Token이 없습니다.",
        )

    access_token = reissue_access_token(refresh_token)
    return TokenResponse(access_token=access_token)


@router.post("/logout", status_code=200)
async def logout_handler(response: Response):
    delete_refresh_token_cookie(response)
    return {"message": "로그아웃 되었습니다."}
