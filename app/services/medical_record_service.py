from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.medical_record_repository import (
    get_medical_record_by_id,
    get_medical_records_by_patient_id,
    get_patient_by_id,
)
from app.schemas.medical_record import (
    MedicalRecordDetailResponse,
    MedicalRecordListResponse,
)


SYMPTOMS_PREVIEW_LENGTH = 100


def _truncate_symptoms(symptoms: str) -> str:
# 100자를 초과하는 증상은 100자까지 표시하고 말줄임표를 붙인다

    if len(symptoms) <= SYMPTOMS_PREVIEW_LENGTH:
        return symptoms

    return f"{symptoms[:SYMPTOMS_PREVIEW_LENGTH]}..."



async def get_patient_medical_records(
    db: AsyncSession,
    patient_id: int,
) -> list[MedicalRecordListResponse]:
# REQ-MDR-002. 특정 환자의 진료기록 목록을 조회한다

    patient = await get_patient_by_id(db, patient_id)

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
# REQ-MDR-003. 특정 진료기록의 상세 내용을 조회한다

    record = await get_medical_record_by_id(
        db=db,
        record_id=record_id,
    )

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="진료기록을 찾을 수 없습니다.",
        )

    # TODO(팀 확인 필요)
    # REQ-MDR-001 담당자의 X-Ray 저장 정책이 확정되면
    # Repository의 X-Ray URL 조회 함수를 호출해 교체합니다.
    #
    # 예:
    # xray_image_url = await get_xray_image_url_by_record_id(
    #     db=db,
    #     record_id=record_id,
    # )

    xray_image_url: str | None = None

    return MedicalRecordDetailResponse(
        id=record.id,
        chart_number=record.chart_number,
        symptoms=record.symptoms,
        xray_image_url=xray_image_url,
        created_at=record.created_at,
    )