from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.dependencies.auth import get_current_user, require_roles
from app.models.enums import Department, Gender, Role
from app.models.user import User
from app.schemas.patient import (
    PatientCreateRequest,
    PatientDetailResponse,
    PatientListResponse,
)
from app.services.patient_service import get_patient, list_patients, register_patient

router = APIRouter(prefix="/api/v1/patients", tags=["patients"])


async def _require_medical_staff(
    current_user: User = Depends(get_current_user),
) -> User:
    """MEDICAL 부서의 STAFF 또는 ADMIN만 통과시킨다."""
    if current_user.role == Role.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="접근 권한이 없습니다.",
        )
    if current_user.department != Department.MEDICAL:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="의료인만 접근 가능합니다.",
        )
    return current_user


_require_staff_or_admin = require_roles(Role.STAFF, Role.ADMIN)


@router.get("", response_model=PatientListResponse, status_code=status.HTTP_200_OK)
async def list_patients_handler(
    current_user: User = Depends(_require_staff_or_admin),
    db: AsyncSession = Depends(async_get_db),
    name: Annotated[
        str | None,
        Query(min_length=1, max_length=30, description="환자 이름 검색어"),
    ] = None,
    gender: Annotated[
        Gender | None,
        Query(description="성별 필터"),
    ] = None,
    min_age: Annotated[
        int | None,
        Query(ge=0, le=150, description="최소 나이"),
    ] = None,
    max_age: Annotated[
        int | None,
        Query(ge=0, le=150, description="최대 나이"),
    ] = None,
    page: Annotated[
        int,
        Query(ge=1, description="조회할 페이지 번호"),
    ] = 1,
    size: Annotated[
        int,
        Query(ge=1, le=100, description="페이지당 환자 수"),
    ] = 20,
) -> PatientListResponse:
    """REQ-PTNT-002. 환자 목록 조회."""
    return await list_patients(
        db,
        name=name,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
        page=page,
        size=size,
    )


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
