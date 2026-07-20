import asyncio

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db.databases import async_get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.schemas.medical_record import (
    MedicalRecordDetailResponse,
    MedicalRecordListResponse,
)
from app.services.medical_record_service import (
    get_medical_record_detail,
    get_patient_medical_records,
)


router = APIRouter(
    prefix="/api/v1",
    tags=["medical-records"],
)


# NFR-MDR-001
# 진료기록 API의 최대 처리시간
MEDICAL_RECORD_API_TIMEOUT_SECONDS = 3.0


@router.get(
    "/patients/{patient_id}/medical-records",
    response_model=list[MedicalRecordListResponse],
)
async def get_patient_medical_records_handler(
    patient_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user),
) -> list[MedicalRecordListResponse]:
# REQ-MDR-002 / NFR-MDR-001. 특정 환자의 진료기록 목록 조회


    # TODO(팀 확인 필요)
    # 현재는 로그인 여부만 검증합니다.
    # STAFF, ADMIN 또는 부서별 최종 접근 정책이 정해지면
    # get_current_user를 require_roles 또는 공통 권한 Dependency로
    # 교체해야 합니다.

    _ = current_user

    try:
        async with asyncio.timeout(
            MEDICAL_RECORD_API_TIMEOUT_SECONDS
        ):
            return await get_patient_medical_records(
                db=db,
                patient_id=patient_id,
            )

    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="진료기록 조회 처리시간이 3초를 초과했습니다.",
        ) from exc


@router.get(
    "/medical-records/{record_id}",
    response_model=MedicalRecordDetailResponse,
)
async def get_medical_record_detail_handler(
    record_id: int,
    db: AsyncSession = Depends(async_get_db),
    current_user: User = Depends(get_current_user),
) -> MedicalRecordDetailResponse:
# REQ-MDR-003 / NFR-MDR-001. 특정 진료기록 상세 조회


    # TODO(팀 확인 필요)
    # 현재는 로그인 여부만 검증합니다.
    # STAFF, ADMIN 또는 부서별 최종 접근 정책이 정해지면
    # get_current_user를 require_roles 또는 공통 권한 Dependency로
    # 교체해야 합니다.

    _ = current_user

    try:
        async with asyncio.timeout(
            MEDICAL_RECORD_API_TIMEOUT_SECONDS
        ):
            return await get_medical_record_detail(
                db=db,
                record_id=record_id,
            )

    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="진료기록 조회 처리시간이 3초를 초과했습니다.",
        ) from exc