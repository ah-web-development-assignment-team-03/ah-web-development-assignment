# app/schemas/medical_record.py
"""진료 기록 요청/응답 스키마 (REQ-MDR-001)

- 등록 요청은 X-Ray 이미지 업로드 때문에 multipart/form-data 로 받으므로
  요청용 스키마 대신 라우터에서 Form / File 파라미터를 사용한다.
- 응답 네이밍은 A의 PatientDetailResponse 패턴을 따른다.
"""
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class XrayImageResponse(BaseModel):
    """기존 XrayImage 모델(app/models/xray_image.py) 필드 기준."""

    id: int
    image_url: str
    shooting_datetime: datetime

    model_config = ConfigDict(from_attributes=True)


class MedicalRecordDetailResponse(BaseModel):
    id: int
    patient_id: int
    chart_number: str
    symptoms: str
    created_at: datetime
    updated_at: datetime | None
    xray_image: XrayImageResponse  # 별도 xray_images 테이블에 저장된 이미지 정보

    model_config = ConfigDict(from_attributes=True)
