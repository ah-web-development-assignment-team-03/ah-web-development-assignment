# app/apis/medical_records.py
"""진료 기록 등록 API 라우터 (REQ-MDR-001)

POST /api/v1/patients/{patient_id}/medical-records
- X-Ray 이미지 업로드가 포함되므로 multipart/form-data 로 요청받는다.
- REQ-MDR-001은 "사내 의료인 역할" 전용 -> 공용 require_medical_staff 의존성 사용.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.dependencies.auth import require_medical_staff
from app.models.user import User
from app.schemas.medical_record import MedicalRecordDetailResponse
from app.services import medical_record_service

router = APIRouter(prefix="/api/v1/patients", tags=["medical-records"])


@router.post(
    "/{patient_id}/medical-records",
    response_model=MedicalRecordDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medical_record_handler(
    patient_id: int,
    chart_number: str = Form(
        ..., max_length=50, description="진료 차트 넘버 (중복 불가, 최대 50자)"
    ),
    symptoms: str = Form(..., description="진료된 증상"),
    xray_image: UploadFile = File(..., description="촬영된 흉부 X-Ray 이미지 (jpg/png, 10MB 이하)"),
    shooting_datetime: datetime | None = Form(
        None, description="X-Ray 촬영 일시 (미입력 시 등록 시각으로 저장)"
    ),
    current_user: User = Depends(require_medical_staff),
    db: AsyncSession = Depends(async_get_db),
) -> MedicalRecordDetailResponse:
    """REQ-MDR-001. X-Ray 이미지를 포함한 진료 기록 등록.

    이미지는 서버 로컬 저장소(media/xray/)에 저장되며,
    이미지 정보(경로·업로더·촬영일시)는 별도 xray_images 테이블에 기록된다.
    """
    record = await medical_record_service.create_medical_record(
        db,
        patient_id=patient_id,
        uploader_id=current_user.id,
        chart_number=chart_number,
        symptoms=symptoms,
        xray_image=xray_image,
        shooting_datetime=shooting_datetime,
    )
    return MedicalRecordDetailResponse.model_validate(record)
