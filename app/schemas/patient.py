from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import Gender


class PatientCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    age: int = Field(..., ge=0, le=150)
    gender: Gender | None = None
    phone: str = Field(..., min_length=1, max_length=11)


class PatientUpdateRequest(BaseModel):
    """REQ-PTNT-004. 수정 가능한 항목은 이름과 연락처뿐이다."""

    name: str | None = Field(default=None, min_length=1, max_length=30)
    phone: str | None = Field(default=None, min_length=1, max_length=11)


class PatientDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: Gender | None
    phone: str
    created_at: datetime
    updated_at: datetime | None


class PatientListResponse(BaseModel):
    items: list[PatientDetailResponse]
    total: int
    page: int
    size: int
