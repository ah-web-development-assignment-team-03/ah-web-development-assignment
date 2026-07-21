# app/schemas/medical_record.py
"""진료기록 요청·응답 스키마.

- REQ-MDR-001: 진료기록 등록
- REQ-MDR-002: 환자별 진료기록 목록 조회
- REQ-MDR-003: 진료기록 상세 조회
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class XrayImageResponse(BaseModel):
    """진료기록에 등록된 X-Ray 이미지 응답."""

    id: int
    image_url: str
    shooting_datetime: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicalRecordListResponse(BaseModel):
    """REQ-MDR-002 진료기록 목록 항목 응답."""

    id: int
    chart_number: str
    symptoms: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicalRecordDetailResponse(BaseModel):
    """REQ-MDR-001 등록 및 REQ-MDR-003 상세 조회 응답."""

    id: int
    chart_number: str
    symptoms: str
    created_at: datetime

    # 등록 응답에서 사용하는 필드
    patient_id: int | None = None
    updated_at: datetime | None = None
    xray_image: XrayImageResponse | None = None

    # 상세 조회 응답에서 사용하는 필드
    xray_image_url: str | None = None

    model_config = ConfigDict(from_attributes=True)