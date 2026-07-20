from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.models.patients import Patient


async def get_patient_by_id(
    db: AsyncSession,
    patient_id: int,
) -> Patient | None:
# 환자 존재 여부 확인용 조회

    result = await db.execute(
        select(Patient).where(Patient.id == patient_id)
    )
    return result.scalar_one_or_none()



async def get_medical_records_by_patient_id(
    db: AsyncSession,
    patient_id: int,
) -> list[MedicalRecord]:
# REQ-MDR-002. 특정 환자의 진료기록을 최신순으로 조회한다

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
# REQ-MDR-003. 진료기록 ID로 상세 조회한다

    result = await db.execute(
        select(MedicalRecord).where(
            MedicalRecord.id == record_id
        )
    )

    return result.scalar_one_or_none()


# TODO(팀 확인 필요)
#
# REQ-MDR-001 담당자와 아래 사항을 확정한 뒤 구현합니다.
#
# 1. 진료기록 한 건에 X-Ray 이미지를 한 장만 허용하는지
# 2. 여러 장이면 첫 이미지와 최근 이미지 중 무엇을 반환하는지
# 3. XrayImage.image_url에 저장되는 값이
#    "/media/..." 형식인지 전체 URL인지
#
# 확정 후 예상 함수 형태:
# async def get_xray_image_url_by_record_id(
#     db: AsyncSession,
#     record_id: int,
# ) -> str | None:
#     ...