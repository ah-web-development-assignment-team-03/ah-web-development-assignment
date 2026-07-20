from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patients import Patient
from app.repositories.patient_repository import create_patient, get_patient_by_id
from app.schemas.patient import PatientCreateRequest


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
