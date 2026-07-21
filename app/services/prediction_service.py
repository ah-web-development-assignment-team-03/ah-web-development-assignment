"""AI 폐렴 예측 결과 Service (REQ-PRED-002).

REQ-PRED-001(예측 실행)은 별도 담당(#49)에서 구현하며,
본 파일은 조회(목록) 로직만 담당한다.
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import prediction_repository
from app.repositories.medical_record_repository import get_medical_record_by_id
from app.schemas.prediction import (
    PredictionResultItem,
    PredictionResultListResponse,
)


async def get_predictions_for_record(
    db: AsyncSession,
    record_id: int,
    *,
    page: int,
    size: int,
) -> PredictionResultListResponse:
    """REQ-PRED-002. 진료기록의 AI 폐렴 예측 결과를 목록으로 조회한다."""

    record = await get_medical_record_by_id(db=db, record_id=record_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )

    results = await prediction_repository.get_predictions_by_record_id(
        db=db,
        record_id=record_id,
        page=page,
        size=size,
    )

    total = await prediction_repository.count_predictions_by_record_id(
        db=db,
        record_id=record_id,
    )

    items = [
        PredictionResultItem(
            id=result.id,
            is_pneumonia=result.is_pneumonia,
            confidence=float(result.confidence),
            heatmap_url=result.heatmap_url,
            predicted_at=result.created_at,
            ai_model=result.ai_model,
        )
        for result in results
    ]

    return PredictionResultListResponse(
        items=items,
        page=page,
        size=size,
        total=total,
    )
