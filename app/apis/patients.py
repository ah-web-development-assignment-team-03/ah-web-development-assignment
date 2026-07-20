from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.dependencies.auth import require_medical_staff as _require_medical_staff, require_roles
from app.models.enums import Department, Role
from app.models.user import User
from app.schemas.patient import PatientCreateRequest, PatientDetailResponse
from app.services.patient_service import get_patient, register_patient

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])



_require_staff_or_admin = require_roles(Role.STAFF, Role.ADMIN)


@router.post("", response_model=PatientDetailResponse, status_code=status.HTTP_201_CREATED)
async def register_patient_handler(
    request: PatientCreateRequest,
    current_user: User = Depends(_require_medical_staff),
    db: AsyncSession = Depends(async_get_db),
) -> PatientDetailResponse:
    """REQ-PTNT-001. 환자 정보 등록."""
    patient = await register_patient(db, request)
    return PatientDetailResponse.model_validate(patient)


@router.get("/{patient_id}", response_model=PatientDetailResponse)
async def get_patient_handler(
    patient_id: int,
    current_user: User = Depends(_require_staff_or_admin),
    db: AsyncSession = Depends(async_get_db),
) -> PatientDetailResponse:
    """REQ-PTNT-003. 환자 정보 상세 조회."""
    patient = await get_patient(db, patient_id)
    return PatientDetailResponse.model_validate(patient)
