# app/services/medical_record_service.py
"""진료 기록 Service (REQ-MDR-001, NFR-MDR-001)

처리 순서:
  1. 환자 존재 확인 — A의 get_patient() 재사용 (없으면 내부에서 404 raise)
  2. 차트 넘버 중복 검사 (chart_number UNIQUE) — 중복 시 409
  3. 이미지 형식 검증 (jpg/png 외 422)
  4. X-Ray 이미지를 서버 로컬 저장소(media/xray/)에 저장
  5. medical_records + xray_images 두 테이블에 INSERT 후 commit
     (실패 시 rollback + 저장한 파일 삭제)
"""
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.repositories import medical_record_repository
# A(환자 담당)의 서비스 함수 재사용 — 인터페이스 계약 항목이므로 직접 쿼리하지 않는다
from app.services.patient_service import get_patient

# C의 환자 삭제 로직이 media/ 폴더 기준으로 X-Ray 파일을 삭제하므로 경로를 통일한다.
# 하위 폴더(xray/) 사용 여부는 C와 협의 후 확정할 것.
MEDIA_DIR = Path("media") / "xray"
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png"}


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
    # 1. 환자 존재 확인 (없으면 get_patient 내부에서 404 raise)
    await get_patient(db, patient_id)

    # 2. 차트 넘버 중복 검사 (UNIQUE 제약)
    existing = await medical_record_repository.get_medical_record_by_chart_number(
        db, chart_number
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Chart number '{chart_number}' already exists",
        )

    # 3. 이미지 형식 검증
    if xray_image.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="X-Ray image must be a jpg or png file",
        )

    # 4. 이미지 로컬 저장 (파일명 충돌 방지를 위해 uuid 사용)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    extension = Path(xray_image.filename or "").suffix or ".png"
    filename = f"{patient_id}_{uuid.uuid4().hex}{extension}"
    save_path = MEDIA_DIR / filename

    content = await xray_image.read()
    save_path.write_bytes(content)

    # 5. 두 테이블 INSERT — 하나의 트랜잭션으로 묶고 commit은 Service 책임
    #    shooting_datetime 은 NOT NULL 컬럼: 입력이 없으면 등록 시각으로 대체
    #    (촬영 일시를 요청 항목으로 받을지는 팀 협의 대상)
    try:
        record = await medical_record_repository.create_medical_record(
            db,
            patient_id=patient_id,
            chart_number=chart_number,
            symptoms=symptoms,
        )
        image = await medical_record_repository.create_xray_image(
            db,
            record_id=record.id,
            uploader_id=uploader_id,
            image_url=str(save_path),
            shooting_datetime=shooting_datetime or datetime.now(),
        )
        await db.commit()
    except Exception:
        await db.rollback()
        save_path.unlink(missing_ok=True)  # DB 실패 시 고아 파일 정리
        raise

    # server_default(created_at) 값 로드 및 응답 조립
    await db.refresh(record)
    record.xray_image = image  # 응답 스키마(MedicalRecordDetailResponse)용 임시 속성
    return record
