"""AI 폐렴 예측 결과 Repository (REQ-PRED-002).

팀 트랜잭션 정책:
- Repository는 조회(add + flush 포함)까지만 담당
- commit / rollback은 Service 계층 책임
"""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_analysis_result import AIAnalysisResult


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
