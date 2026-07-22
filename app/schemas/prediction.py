from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PredictionResultItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_pneumonia: bool
    confidence: float
    heatmap_url: str | None
    predicted_at: datetime
    ai_model: str


class PredictionResultListResponse(BaseModel):
    """REQ-PRED-002 목록 조회 응답."""

    items: list[PredictionResultItem]
    page: int
    size: int
    total: int

class PredictionRunResponse(PredictionResultItem):
    """REQ-PRED-001 전용 — 캐시 히트 여부를 함께 반환한다."""

    cached: bool
