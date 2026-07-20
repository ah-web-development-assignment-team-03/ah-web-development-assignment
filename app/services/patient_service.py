from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patients import GenderEnum, Patient
from app.repositories.patient_repository import (
    count_patients,
    create_patient,
    get_patient_by_id,
    get_patients,
)
from app.schemas.patient import (
    PatientCreateRequest,
    PatientDetailResponse,
    PatientListResponse,
)


async def register_patient(db: AsyncSession, data: PatientCreateRequest) -> Patient:
    """REQ-PTNT-001. 환자 정보를 등록한다."""
    return await create_patient(
        db,
        name=data.name,
        age=data.age,
        gender=data.gender,
        phone=data.phone,
    )


async def get_patient(db: AsyncSession, patient_id: int) -> Patient:
    """REQ-PTNT-003. 환자 상세 정보를 조회한다."""
    patient = await get_patient_by_id(db, patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="환자를 찾을 수 없습니다.",
        )
    return patient


async def list_patients(
    db: AsyncSession,
    *,
    name: str | None,
    gender: GenderEnum | None,
    min_age: int | None,
    max_age: int | None,
    page: int,
    size: int,
) -> PatientListResponse:
    """REQ-PTNT-002. 환자 목록을 검색·필터·페이지 단위로 조회한다."""
    normalized_name = name.strip() if name is not None else None
    if normalized_name == "":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="이름 검색어는 공백일 수 없습니다.",
        )
    if min_age is not None and max_age is not None and min_age > max_age:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="min_age는 max_age보다 클 수 없습니다.",
        )

    filters = {
        "name": normalized_name,
        "gender": gender,
        "min_age": min_age,
        "max_age": max_age,
    }
    patients = await get_patients(
        db,
        **filters,
        offset=(page - 1) * size,
        limit=size,
    )
    total = await count_patients(db, **filters)

    return PatientListResponse(
        items=[PatientDetailResponse.model_validate(patient) for patient in patients],
        total=total,
        page=page,
        size=size,
    )
