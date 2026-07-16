from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db.databases import async_get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.services.auth_service import login, reissue_access_token

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])

REFRESH_TOKEN_COOKIE = "refresh_token"
REFRESH_TOKEN_MAX_AGE = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


@router.post("/login", response_model=TokenResponse, status_code=200)
async def login_handler(
    request: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(async_get_db),
):
    access_token, refresh_token = await login(db, request.email, request.password)

    response.set_cookie(
        key=REFRESH_TOKEN_COOKIE,
        value=refresh_token,
        httponly=True,
        max_age=REFRESH_TOKEN_MAX_AGE,
        samesite="lax",
        secure=False,
    )

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
    response.delete_cookie(key=REFRESH_TOKEN_COOKIE, httponly=True, samesite="lax")
    return {"message": "로그아웃 되었습니다."}
