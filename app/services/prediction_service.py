"""REQ-PRED-001 폐렴 예측 Service.

처리 흐름:
  1. 진료기록 존재 확인 (404)
  2. X-ray 이미지 존재 확인 (404)
  3. 캐시 조회 (record_id + ai_model)
     - 히트: 저장된 결과 반환 (cached=True)
     - 미스: predict() → 저장 → 반환 (cached=False)
  4. IntegrityError(동시 요청 충돌) → rollback 후 재조회 → 반환 (cached=True)
"""

from pathlib import Path

import anyio
from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import medical_record_repository
from app.repositories import prediction_repository
from app.schemas.prediction import PredictionRunResponse
from worker.model import MODEL_TAG, predict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _to_response(result, *, cached: bool) -> PredictionRunResponse:
    return PredictionRunResponse(
        id=result.id,
        is_pneumonia=result.is_pneumonia,
        confidence=float(result.confidence),
        heatmap_url=result.heatmap_url,
        predicted_at=result.created_at,
        ai_model=result.ai_model,
        cached=cached,
    )


async def run_prediction(
    db: AsyncSession,
    record_id: int,
) -> PredictionRunResponse:
    """진료기록 ID로 폐렴 예측을 실행하거나 캐시된 결과를 반환한다."""

    # 1. 진료기록 존재 확인
    record = await medical_record_repository.get_medical_record_by_id(db, record_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )

    # 2. X-ray 이미지 존재 확인
    xray = await prediction_repository.get_xray_image_by_record_id(db, record_id)
    if xray is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="예측에 사용할 X-ray 이미지가 없습니다.",
        )

    # 3. 캐시 조회
    cached_result = await prediction_repository.get_cached_result(db, record_id, MODEL_TAG)
    if cached_result is not None:
        return _to_response(cached_result, cached=True)

    # 4. 추론 수행 (CPU 동기 작업 → 스레드 위임)
    image_path = str(_PROJECT_ROOT / xray.image_url)
    try:
        prediction = await anyio.to_thread.run_sync(predict, image_path, abandon_on_cancel=True)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="폐렴 예측 처리 중 오류가 발생했습니다.",
        ) from exc

    # 5. 저장
    try:
        result = await prediction_repository.save_result(
            db,
            record_id=record_id,
            is_pneumonia=prediction["is_pneumonia"],
            confidence=prediction["confidence"],
            heatmap_url=prediction.get("heatmap_url"),
            ai_model=prediction["ai_model"],
        )
        await db.commit()
        await db.refresh(result)
        return _to_response(result, cached=False)

    except IntegrityError:
        # 동시 요청 충돌: 먼저 저장한 쪽이 UNIQUE 제약을 선점함
        await db.rollback()
        saved = await prediction_repository.get_cached_result(db, record_id, MODEL_TAG)
        if saved is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="폐렴 예측 처리 중 오류가 발생했습니다.",
            )
        return _to_response(saved, cached=True)

    except Exception:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="폐렴 예측 처리 중 오류가 발생했습니다.",
        )
