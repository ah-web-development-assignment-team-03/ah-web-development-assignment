import os
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, status
from redis.exceptions import RedisError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import redis_client
from app.repositories import medical_record_repository, prediction_repository
from app.schemas.prediction import (
    PredictionResultItem,
    PredictionResultListResponse,
    PredictionRunResponse,
)


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
MODEL_TAG = os.getenv("AI_MODEL_NAME", "v7_densenet121_5fold")


async def get_predictions_for_record(
    db: AsyncSession,
    record_id: int,
    *,
    page: int,
    size: int,
) -> PredictionResultListResponse:
    """REQ-PRED-002. 진료기록의 AI 폐렴 예측 결과를 목록으로 조회한다."""

    record = await medical_record_repository.get_medical_record_by_id(db=db, record_id=record_id)
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
    """REQ-PRED-001. 진료기록 ID로 폐렴 예측을 실행하거나 캐시된 결과를 반환한다."""

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

    # 4. Redis Queue에 추론 작업을 등록하고 Worker 결과 대기
    image_path = str(_PROJECT_ROOT / xray.image_url)
    task_id = str(uuid4())
    try:
        prediction = await redis_client.enqueue_and_wait(
            {
                "task_id": task_id,
                "image_path": image_path,
                "model_name": MODEL_TAG,
            }
        )
    except redis_client.ResultTimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="AI Worker의 응답 시간이 초과되었습니다.",
        ) from exc
    except RedisError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI 예측 서비스를 일시적으로 사용할 수 없습니다.",
        ) from exc
    except (ValueError, TypeError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI Worker로부터 올바르지 않은 응답을 받았습니다.",
        ) from exc

    if prediction.get("task_id") != task_id:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI Worker 응답의 작업 ID가 일치하지 않습니다.",
        )

    worker_status_code = prediction.get("status_code", status.HTTP_200_OK)
    if not isinstance(worker_status_code, int):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI Worker로부터 올바르지 않은 상태 코드를 받았습니다.",
        )
    if worker_status_code >= status.HTTP_400_BAD_REQUEST:
        if worker_status_code > 599:
            worker_status_code = status.HTTP_502_BAD_GATEWAY
        detail = prediction.get("detail", "AI Worker의 예측 처리에 실패했습니다.")
        raise HTTPException(status_code=worker_status_code, detail=str(detail))

    required_fields = ("is_pneumonia", "confidence", "ai_model")
    if any(field not in prediction for field in required_fields):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="AI Worker 응답에 필수 결과가 없습니다.",
        )

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
