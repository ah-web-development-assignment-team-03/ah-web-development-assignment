from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_result import AIAnalysisResult
from app.models.xray_image import XrayImage


async def get_predictions_by_record_id(
    db: AsyncSession,
    record_id: int,
    *,
    page: int,
    size: int,
) -> list[AIAnalysisResult]:
    """REQ-PRED-002. 진료기록의 예측 결과를 최신순으로 페이지네이션하여 조회한다."""

    offset = (page - 1) * size

    result = await db.execute(
        select(AIAnalysisResult)
        .where(AIAnalysisResult.record_id == record_id)
        .order_by(
            AIAnalysisResult.created_at.desc(),
            AIAnalysisResult.id.desc(),
        )
        .offset(offset)
        .limit(size)
    )

    return list(result.scalars().all())


async def count_predictions_by_record_id(
    db: AsyncSession,
    record_id: int,
) -> int:
    """REQ-PRED-002. 진료기록에 저장된 전체 예측 결과 수를 조회한다."""

    result = await db.execute(
        select(func.count())
        .select_from(AIAnalysisResult)
        .where(AIAnalysisResult.record_id == record_id)
    )

    return result.scalar_one()


async def get_xray_image_by_record_id(
    db: AsyncSession,
    record_id: int,
) -> XrayImage | None:
    """진료기록에 연결된 X-ray 이미지를 최신순으로 1건 조회한다."""
    result = await db.execute(
        select(XrayImage)
        .where(XrayImage.record_id == record_id)
        .order_by(XrayImage.id.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def get_cached_result(
    db: AsyncSession,
    record_id: int,
    ai_model: str,
) -> AIAnalysisResult | None:
    """record_id + ai_model 조합으로 저장된 예측 결과를 조회한다."""
    result = await db.execute(
        select(AIAnalysisResult).where(
            AIAnalysisResult.record_id == record_id,
            AIAnalysisResult.ai_model == ai_model,
        )
    )
    return result.scalar_one_or_none()


async def save_result(
    db: AsyncSession,
    *,
    record_id: int,
    is_pneumonia: bool,
    confidence: float,
    heatmap_url: str | None,
    ai_model: str,
) -> AIAnalysisResult:
    """예측 결과를 저장하고 flush하여 ID를 확보한다."""
    analysis = AIAnalysisResult(
        record_id=record_id,
        is_pneumonia=is_pneumonia,
        confidence=Decimal(str(confidence)),
        heatmap_url=heatmap_url,
        ai_model=ai_model,
    )
    db.add(analysis)
    await db.flush()
    return analysis
