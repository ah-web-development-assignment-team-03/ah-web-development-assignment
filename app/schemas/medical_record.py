from datetime import datetime
from pydantic import BaseModel


# REQ-MDR-002 진료기록 목록 항목 응답
class MedicalRecordListResponse(BaseModel):

    id: int
    chart_number: str
    symptoms: str
    created_at: datetime


# REQ-MDR-003 진료기록 상세 응답
class MedicalRecordDetailResponse(BaseModel):

    id: int
    chart_number: str
    symptoms: str
    xray_image_url: str | None
    created_at: datetime