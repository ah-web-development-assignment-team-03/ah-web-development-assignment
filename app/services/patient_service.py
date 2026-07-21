import logging
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import Gender
from app.models.patients import Patient
from app.repositories.patient_repository import (
    count_patients,
    create_patient,
    get_image_urls_by_patient,
    get_patient_by_id,
    get_patients,
)
from app.repositories.patient_repository import delete_patient as delete_patient_row
from app.repositories.patient_repository import update_patient as update_patient_row
from app.schemas.patient import (
    PatientCreateRequest,
    PatientDetailResponse,
    PatientListResponse,
    PatientUpdateRequest,
)

logger = logging.getLogger(__name__)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]


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
    gender: Gender | None,
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


async def update_patient(
    db: AsyncSession,
    patient_id: int,
    data: PatientUpdateRequest,
) -> Patient:
    """REQ-PTNT-004. 환자의 이름·연락처를 수정한다."""
    patient = await get_patient(db, patient_id)
    return await update_patient_row(db, patient, data)


def _resolve_image_path(image_url: str) -> Path | None:
    """로컬 image_url을 안전한 실제 파일 경로로 변환한다."""
    if not image_url or "://" in image_url:
        return None

    candidate = (_PROJECT_ROOT / image_url.lstrip("/")).resolve()
    if not candidate.is_relative_to(_PROJECT_ROOT) or not candidate.is_file():
        return None
    return candidate


async def delete_patient(db: AsyncSession, patient_id: int) -> None:
    """REQ-PTNT-005. 환자와 관련 데이터를 영구 삭제한다."""
    patient = await get_patient(db, patient_id)
    image_urls = await get_image_urls_by_patient(db, patient_id)
    await delete_patient_row(db, patient)

    for image_url in image_urls:
        path = _resolve_image_path(image_url)
        if path is None:
            logger.warning(
                "X-ray 이미지 경로를 해석할 수 없어 건너뜁니다. patient_id=%s image_url=%s",
                patient_id,
                image_url,
            )
            continue
        try:
            path.unlink()
        except OSError:
            logger.exception(
                "X-ray 이미지 파일 삭제에 실패했습니다. patient_id=%s path=%s",
                patient_id,
                path,
            )
