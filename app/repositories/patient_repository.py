from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.elements import ColumnElement

from app.models.enums import Gender
from app.models.patients import Patient


async def create_patient(
    db: AsyncSession,   # DB 세션
    *,  # 이 위치 이후의 모든 인자는 키워드 인자로 전달되어야 함
    name: str,
    age: int,
    gender: Gender | None,
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


def _patient_list_conditions(
    *,
    name: str | None,
    gender: Gender | None,
    min_age: int | None,
    max_age: int | None,
) -> list[ColumnElement[bool]]:
    conditions: list[ColumnElement[bool]] = []

    if name is not None:
        conditions.append(Patient.name.ilike(f"%{name}%"))
    if gender is not None:
        conditions.append(Patient.gender == gender)
    if min_age is not None:
        conditions.append(Patient.age >= min_age)
    if max_age is not None:
        conditions.append(Patient.age <= max_age)

    return conditions


async def get_patients(
    db: AsyncSession,
    *,
    name: str | None,
    gender: Gender | None,
    min_age: int | None,
    max_age: int | None,
    offset: int,
    limit: int,
) -> Sequence[Patient]:
    """검색·필터 조건에 맞는 환자 목록을 페이지 단위로 조회한다."""
    conditions = _patient_list_conditions(
        name=name,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
    )
    query = select(Patient).order_by(Patient.id).offset(offset).limit(limit)
    if conditions:
        query = query.where(*conditions)

    result = await db.execute(query)
    return result.scalars().all()


async def count_patients(
    db: AsyncSession,
    *,
    name: str | None,
    gender: Gender | None,
    min_age: int | None,
    max_age: int | None,
) -> int:
    """검색·필터 조건에 맞는 전체 환자 수를 조회한다."""
    conditions = _patient_list_conditions(
        name=name,
        gender=gender,
        min_age=min_age,
        max_age=max_age,
    )
    query = select(func.count(Patient.id))
    if conditions:
        query = query.where(*conditions)

    result = await db.execute(query)
    return result.scalar_one()
