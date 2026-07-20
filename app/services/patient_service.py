import logging
from pathlib import Path

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.patients import Patient
from app.repositories.patient_repository import (
    create_patient,
    get_image_urls_by_patient,
    get_patient_by_id,
)
from app.repositories.patient_repository import delete_patient as delete_patient_row
from app.repositories.patient_repository import update_patient as update_patient_row
from app.schemas.patient import PatientCreateRequest, PatientUpdateRequest

logger = logging.getLogger(__name__)

# app/services/patient_service.py -> app/services -> app -> 프로젝트 루트
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


# ── C 구현 영역 (REQ-PTNT-004, 005) ──────────────────────────
async def update_patient(
    db: AsyncSession,
    patient_id: int,
    data: PatientUpdateRequest,
) -> Patient:
    """REQ-PTNT-004. 환자의 이름·연락처를 수정한다.

    존재하지 않는 환자에 대한 404는 get_patient()가 던진다.
    """
    patient = await get_patient(db, patient_id)
    return await update_patient_row(db, patient, data)


def _resolve_image_path(image_url: str) -> Path | None:
    """image_url -> 실제 파일 경로. REQ-MDR-001 저장 규약 확정 시 이 함수만 고친다.

    저장 규약이 아직 정해지지 않았다. 잠정적으로 프로젝트 루트 기준
    상대경로로 가정하고, 해석할 수 없으면 None을 반환해 건너뛴다.
    """
    if not image_url:
        return None

    # 외부 URL(s3, http 등)은 로컬 파일이 아니므로 다룰 수 없다.
    if "://" in image_url:
        return None

    candidate = (_PROJECT_ROOT / image_url.lstrip("/")).resolve()

    # 프로젝트 루트 밖을 가리키면(경로 조작 등) 건드리지 않는다.
    if not candidate.is_relative_to(_PROJECT_ROOT):
        return None

    if not candidate.is_file():
        return None

    return candidate


async def delete_patient(db: AsyncSession, patient_id: int) -> None:
    """REQ-PTNT-005. 환자와 관련 데이터를 영구 삭제한다.

    진료기록·X-ray 레코드는 FK의 ON DELETE CASCADE로 DB가 함께 지운다.
    애플리케이션은 로컬 이미지 파일만 직접 정리한다.
    """
    patient = await get_patient(db, patient_id)

    # 1) DB 행이 사라지기 전에 지울 파일 목록을 먼저 확보한다.
    image_urls = await get_image_urls_by_patient(db, patient_id)

    # 2) DB 삭제 + 커밋. 실패하면 여기서 예외가 올라가고 파일은 건드리지 않는다.
    await delete_patient_row(db, patient)

    # 3) 커밋이 끝난 뒤에만 파일을 지운다.
    #    파일 삭제 실패로 DB를 되돌리면 그 파일을 지울 수단이 사라지므로
    #    로그만 남기고 예외는 올리지 않는다.
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
