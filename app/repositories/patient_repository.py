from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.patients import GenderEnum, Patient
from app.models.xray_image import XrayImage
from app.schemas.patient import PatientUpdateRequest


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


# ── C 구현 영역 (REQ-PTNT-004, 005) ──────────────────────────
async def get_image_urls_by_patient(db: AsyncSession, patient_id: int) -> list[str]:
    """해당 환자에 속한 X-ray 이미지의 image_url 목록을 조회한다.

    환자 삭제(REQ-PTNT-005) 시 DB 행이 CASCADE로 사라지기 전에
    지워야 할 파일 목록을 미리 확보하기 위해 사용한다.
    """
    result = await db.execute(
        select(XrayImage.image_url)
        .join(MedicalRecord, XrayImage.record_id == MedicalRecord.id)
        .where(MedicalRecord.patient_id == patient_id)
    )
    return list(result.scalars().all())


async def update_patient(
    db: AsyncSession,
    patient: Patient,
    data: PatientUpdateRequest,
) -> Patient:
    """전달된 필드만 반영한다. 생략된 필드는 기존 값을 유지한다.

    name·phone 컬럼은 NOT NULL이라 명시적 null은 반영 대상이 아니다.
    (exclude_none으로 걸러 500 대신 기존 값 유지로 처리한다)
    """
    for field, value in data.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(patient, field, value)
    await db.commit()
    await db.refresh(patient)
    return patient


async def delete_patient(db: AsyncSession, patient: Patient) -> None:
    """환자 행을 삭제한다.

    진료기록·X-ray 레코드는 FK의 ON DELETE CASCADE로 DB가 함께 삭제한다.
    """
    await db.delete(patient)
    await db.commit()
