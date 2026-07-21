import asyncio
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.dependencies.auth import require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.prediction import PredictionResultListResponse
from app.services import prediction_service


router = APIRouter(prefix="/api/v1", tags=["predictions"])

# NFR-PRED-002
PREDICTION_API_TIMEOUT_SECONDS = 3.0

# 예측 결과 조회 API 접근 권한
require_prediction_access = require_roles(Role.STAFF, Role.ADMIN)


@router.get(
    "/medical-records/{record_id}/predictions",
    response_model=PredictionResultListResponse,
)
async def get_medical_record_predictions_handler(
    record_id: int,
    page: Annotated[
        int,
        Query(ge=1, description="조회할 페이지 번호"),
    ] = 1,
    size: Annotated[
        int,
        Query(ge=1, le=100, description="페이지당 예측 결과 수"),
    ] = 20,
    current_user: User = Depends(require_prediction_access),
    db: AsyncSession = Depends(async_get_db),
) -> PredictionResultListResponse:
    """REQ-PRED-002. 진료기록의 AI 폐렴 예측 결과를 목록으로 조회한다."""

    _ = current_user

    try:
        async with asyncio.timeout(PREDICTION_API_TIMEOUT_SECONDS):
            return await prediction_service.get_predictions_for_record(
                db=db,
                record_id=record_id,
                page=page,
                size=size,
            )

    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="폐렴 예측 결과 조회 처리시간이 3초를 초과했습니다.",
        ) from exc
