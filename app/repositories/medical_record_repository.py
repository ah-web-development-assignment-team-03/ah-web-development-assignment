"""진료 기록 Repository (REQ-MDR-001, REQ-MDR-002, REQ-MDR-003).

팀 트랜잭션 정책:
- Repository는 add + flush까지만 담당
- commit / rollback은 Service 계층 책임
"""

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.xray_image import XrayImage


async def get_medical_records_by_patient_id(
    db: AsyncSession,
    patient_id: int,
) -> list[MedicalRecord]:
    """REQ-MDR-002. 특정 환자의 진료기록을 최신순으로 조회한다."""

    result = await db.execute(
        select(MedicalRecord)
        .where(MedicalRecord.patient_id == patient_id)
        .order_by(
            MedicalRecord.created_at.desc(),
            MedicalRecord.id.desc(),
        )
    )

    return list(result.scalars().all())


async def get_medical_record_by_id(
    db: AsyncSession,
    record_id: int,
) -> MedicalRecord | None:
    """REQ-MDR-003. 진료기록 ID로 상세 내용을 조회한다."""

    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.id == record_id
        )
    )

    return result.scalar_one_or_none()


async def get_medical_record_by_chart_number(
    db: AsyncSession,
    chart_number: str,
) -> MedicalRecord | None:
    """차트 번호 중복 확인을 위해 진료기록을 단건 조회한다."""

    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.chart_number == chart_number
        )
    )

    return result.scalar_one_or_none()


async def create_medical_record(
    db: AsyncSession,
    *,
    patient_id: int,
    chart_number: str,
    symptoms: str,
) -> MedicalRecord:
    """진료기록을 추가하고 flush하여 ID를 확보한다."""

    record = MedicalRecord(
        patient_id=patient_id,
        chart_number=chart_number,
        symptoms=symptoms,
    )

    db.add(record)
    await db.flush()

    return record


async def create_xray_image(
    db: AsyncSession,
    *,
    record_id: int,
    uploader_id: int,
    image_url: str,
    shooting_datetime: datetime,
) -> XrayImage:
    """X-Ray 이미지 정보를 진료기록과 같은 트랜잭션에 추가한다."""

    image = XrayImage(
        record_id=record_id,
        uploader_id=uploader_id,
        image_url=image_url,
        shooting_datetime=shooting_datetime,
    )

    db.add(image)
    await db.flush()

    return image