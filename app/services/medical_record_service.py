# app/services/medical_record_service.py
"""진료 기록 Service (REQ-MDR-001, REQ-MDR-002, REQ-MDR-003).

Repository는 add + flush까지만 담당하고,
commit / rollback은 Service 계층에서 담당한다.
"""

import uuid
from datetime import datetime
from pathlib import Path

import anyio
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.repositories import (
    medical_record_repository,
    patient_repository,
)
from app.repositories.medical_record_repository import (
    get_medical_record_by_id,
    get_medical_records_by_patient_id,
)
from app.schemas.medical_record import (
    MedicalRecordDetailResponse,
    MedicalRecordListResponse,
)
from app.services.patient_service import get_patient


SYMPTOMS_PREVIEW_LENGTH = 100

MEDIA_DIR = Path("media") / "xray"

CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

MAX_FILE_SIZE = 10 * 1024 * 1024


def _truncate_symptoms(symptoms: str) -> str:
    """100자를 초과하는 증상은 100자까지 표시하고 말줄임표를 붙인다."""

    if len(symptoms) <= SYMPTOMS_PREVIEW_LENGTH:
        return symptoms

    return f"{symptoms[:SYMPTOMS_PREVIEW_LENGTH]}…"


async def get_patient_medical_records(
    db: AsyncSession,
    patient_id: int,
) -> list[MedicalRecordListResponse]:
    """REQ-MDR-002. 특정 환자의 진료기록 목록을 조회한다."""

    patient = await patient_repository.get_patient_by_id(
        db=db,
        patient_id=patient_id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="환자를 찾을 수 없습니다.",
        )

    records = await get_medical_records_by_patient_id(
        db=db,
        patient_id=patient_id,
    )

    return [
        MedicalRecordListResponse(
            id=record.id,
            chart_number=record.chart_number,
            symptoms=_truncate_symptoms(record.symptoms),
            created_at=record.created_at,
        )
        for record in records
    ]


async def get_medical_record_detail(
    db: AsyncSession,
    record_id: int,
) -> MedicalRecordDetailResponse:
    """REQ-MDR-003. 특정 진료기록의 상세 내용을 조회한다."""

    record = await get_medical_record_by_id(
        db=db,
        record_id=record_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )

    # X-Ray 조회 정책이 확정되기 전까지 None 반환
    xray_image_url: str | None = None

    return MedicalRecordDetailResponse(
        id=record.id,
        chart_number=record.chart_number,
        symptoms=record.symptoms,
        xray_image_url=xray_image_url,
        created_at=record.created_at,
    )


async def create_medical_record(
    db: AsyncSession,
    *,
    patient_id: int,
    uploader_id: int,
    chart_number: str,
    symptoms: str,
    xray_image: UploadFile,
    shooting_datetime: datetime | None = None,
) -> MedicalRecord:
    """REQ-MDR-001. 진료기록과 X-Ray 이미지를 등록한다."""

    # 1. 환자 존재 확인
    await get_patient(db, patient_id)

    # 2. 차트 번호 중복 확인
    existing = (
        await medical_record_repository.get_medical_record_by_chart_number(
            db=db,
            chart_number=chart_number,
        )
    )

    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Chart number '{chart_number}' already exists",
        )

    # 3. 이미지 형식 검증
    extension = CONTENT_TYPE_EXTENSIONS.get(
        xray_image.content_type or ""
    )

    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="X-Ray image must be a jpg or png file",
        )

    # 4. 이미지 크기 검증
    content = await xray_image.read()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="X-Ray image must be 10MB or smaller",
        )

    # 5. 이미지 저장
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    filename = f"{patient_id}_{uuid.uuid4().hex}{extension}"
    save_path = MEDIA_DIR / filename

    await anyio.to_thread.run_sync(
        save_path.write_bytes,
        content,
    )

    # 6. 진료기록 및 이미지 DB 저장
    try:
        record = await medical_record_repository.create_medical_record(
            db=db,
            patient_id=patient_id,
            chart_number=chart_number,
            symptoms=symptoms,
        )

        image = await medical_record_repository.create_xray_image(
            db=db,
            record_id=record.id,
            uploader_id=uploader_id,
            image_url=str(save_path),
            shooting_datetime=shooting_datetime or datetime.now(),
        )

        await db.commit()

    except IntegrityError:
        await db.rollback()
        save_path.unlink(missing_ok=True)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Chart number '{chart_number}' already exists",
        )

    except Exception:
        await db.rollback()
        save_path.unlink(missing_ok=True)
        raise

    await db.refresh(record)
    await db.refresh(image)

    # 현재 응답 조립을 위해 임시 속성으로 이미지 객체 연결
    record.xray_image = image

    return record