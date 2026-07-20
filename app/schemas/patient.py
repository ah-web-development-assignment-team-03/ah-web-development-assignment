from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.patients import GenderEnum


class PatientCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    age: int = Field(..., ge=0, le=150)
    gender: GenderEnum
    phone: str = Field(..., min_length=1, max_length=11)


# ── C 구현 영역 (REQ-PTNT-004, 005) ──────────────────────────
class PatientUpdateRequest(BaseModel):
    """REQ-PTNT-004. 수정 가능한 항목은 이름과 연락처뿐이다.

    두 필드 모두 선택 항목이며, 전달된 필드만 반영한다(Partial 수정).
    """

    name: str | None = Field(default=None, min_length=1, max_length=30)
    phone: str | None = Field(default=None, min_length=1, max_length=11)


# ── C 구현 영역 끝 ──────────────────────────
class PatientDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: GenderEnum
    phone: str
    created_at: datetime
    updated_at: datetime | None
