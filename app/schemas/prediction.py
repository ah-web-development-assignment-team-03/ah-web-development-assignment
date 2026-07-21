# app/schemas/prediction.py
"""AI 폐렴 예측 결과 요청·응답 스키마.

- REQ-PRED-001: 폐렴 예측 실행 (PR #49)
- REQ-PRED-002: 폐렴 예측 결과 목록 조회 (본 담당 범위)
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PredictionResultItem(BaseModel):
    """REQ-PRED-001/002 공용 예측 결과 항목.

    heatmap_url은 현재 모델(predict())이 heatmap을 생성하지 않아
    nullable 처리가 필요하다는 점이 리뷰에서 논의 중이므로,
    DB 컬럼(nullable=False) 확정 전까지는 응답 타입만 Optional로 열어둔다.
    """

    id: int
    is_pneumonia: bool
    confidence: float
    heatmap_url: str | None
    predicted_at: datetime
    ai_model: str

    model_config = ConfigDict(from_attributes=True)


class PredictionResultListResponse(BaseModel):
    """REQ-PRED-002 목록 조회 응답."""

    items: list[PredictionResultItem]
    page: int
    size: int
    total: int
