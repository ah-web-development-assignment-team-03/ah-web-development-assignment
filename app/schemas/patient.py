from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.patients import GenderEnum


class PatientCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=30)
    age: int = Field(..., ge=0, le=150)
    gender: GenderEnum
    phone: str = Field(..., min_length=1, max_length=11)


class PatientDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    age: int
    gender: GenderEnum
    phone: str
    created_at: datetime
    updated_at: datetime | None
