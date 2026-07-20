from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patients import GenderEnum, Patient


async def create_patient(
    db: AsyncSession,   # DB 세션
    *,  # 이 위치 이후의 모든 인자는 키워드 인자로 전달되어야 함
    name: str,
    age: int,
    gender: GenderEnum,
    phone: str,
) -> Patient:
    patient = Patient(name=name, age=age, gender=gender, phone=phone)
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


async def get_patient_by_id(db: AsyncSession, patient_id: int) -> Patient | None:
    result = await db.execute(select(Patient).where(Patient.id == patient_id))
    return result.scalar_one_or_none()
