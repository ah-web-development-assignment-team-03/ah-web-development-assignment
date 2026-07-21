# app/repositories/medical_record_repository.py
"""진료 기록 Repository (REQ-MDR-001)

팀 트랜잭션 정책:
- Repository는 add + flush 까지만 담당
- commit / rollback 은 Service 계층 책임
"""
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.xray_image import XrayImage


async def get_medical_record_by_chart_number(
    db: AsyncSession, chart_number: str
) -> MedicalRecord | None:
    """차트 넘버로 진료 기록 단건 조회. (chart_number UNIQUE 중복 검사용)"""
    result = await db.execute(
        select(MedicalRecord).where(MedicalRecord.chart_number == chart_number)
    )
    return result.scalar_one_or_none()


async def create_medical_record(
    db: AsyncSession,
    *,
    patient_id: int,
    chart_number: str,
    symptoms: str,
) -> MedicalRecord:
    """진료 기록 INSERT. flush로 PK(id)까지만 확보한다."""
    record = MedicalRecord(
        patient_id=patient_id,
        chart_number=chart_number,
        symptoms=symptoms,
    )
    db.add(record)
    await db.flush()  # record.id 확보 (commit은 Service에서)
    return record


async def create_xray_image(
    db: AsyncSession,
    *,
    record_id: int,
    uploader_id: int,
    image_url: str,
    shooting_datetime: datetime,
) -> XrayImage:
    """X-Ray 이미지 INSERT. 진료 기록과 같은 트랜잭션에서 처리한다.

    기존 XrayImage 모델 필드 기준: record_id, uploader_id, image_url, shooting_datetime
    """
    image = XrayImage(
        record_id=record_id,
        uploader_id=uploader_id,
        image_url=image_url,
        shooting_datetime=shooting_datetime,
    )
    db.add(image)
    await db.flush()
    return image
