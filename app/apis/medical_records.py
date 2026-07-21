import asyncio
from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.dependencies.auth import require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.medical_record import (
    MedicalRecordDetailResponse,
    MedicalRecordListResponse,
)
from app.services import medical_record_service


router = APIRouter(
    prefix="/api/v1",
    tags=["medical-records"],
)

# NFR-MDR-001
MEDICAL_RECORD_API_TIMEOUT_SECONDS = 3.0

# 진료기록 API 접근 권한
require_medical_record_access = require_roles(
    Role.STAFF,
    Role.ADMIN,
)


@router.post(
    "/patients/{patient_id}/medical-records",
    response_model=MedicalRecordDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_medical_record_handler(
    patient_id: int,
    chart_number: str = Form(
        ...,
        max_length=50,
        description="진료 차트 넘버 (중복 불가, 최대 50자)",
    ),
    symptoms: str = Form(
        ...,
        description="진료된 증상",
    ),
    xray_image: UploadFile = File(
        ...,
        description="촬영된 흉부 X-Ray 이미지 (jpg/png, 10MB 이하)",
    ),
    shooting_datetime: datetime | None = Form(
        None,
        description="X-Ray 촬영 일시 (미입력 시 등록 시각으로 저장)",
    ),
    current_user: User = Depends(require_medical_record_access),
    db: AsyncSession = Depends(async_get_db),
) -> MedicalRecordDetailResponse:
    """REQ-MDR-001. X-Ray 이미지를 포함한 진료기록을 등록한다."""

    record = await medical_record_service.create_medical_record(
        db=db,
        patient_id=patient_id,
        uploader_id=current_user.id,
        chart_number=chart_number,
        symptoms=symptoms,
        xray_image=xray_image,
        shooting_datetime=shooting_datetime,
    )

    return MedicalRecordDetailResponse.model_validate(record)


@router.get(
    "/patients/{patient_id}/medical-records",
    response_model=list[MedicalRecordListResponse],
)
async def get_patient_medical_records_handler(
    patient_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_medical_record_access),
) -> list[MedicalRecordListResponse]:
    """REQ-MDR-002. 특정 환자의 진료기록 목록을 조회한다."""

    _ = current_user

    try:
        async with asyncio.timeout(
            MEDICAL_RECORD_API_TIMEOUT_SECONDS
        ):
            return await medical_record_service.get_patient_medical_records(
                db=db,
                patient_id=patient_id,
            )

    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="진료기록 조회 처리시간이 3초를 초과했습니다.",
        ) from exc


@router.get(
    "/medical-records/{record_id}",
    response_model=MedicalRecordDetailResponse,
)
async def get_medical_record_detail_handler(
    record_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(require_medical_record_access),
) -> MedicalRecordDetailResponse:
    """REQ-MDR-003. 특정 진료기록의 상세 내용을 조회한다."""

    _ = current_user

    try:
        async with asyncio.timeout(
            MEDICAL_RECORD_API_TIMEOUT_SECONDS
        ):
            return await medical_record_service.get_medical_record_detail(
                db=db,
                record_id=record_id,
            )

    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="진료기록 조회 처리시간이 3초를 초과했습니다.",
        ) from exc