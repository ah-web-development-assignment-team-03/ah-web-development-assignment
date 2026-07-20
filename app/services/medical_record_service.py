# app/services/medical_record_service.py
"""진료 기록 Service (REQ-MDR-001, NFR-MDR-001)

처리 순서:
  1. 환자 존재 확인 — get_patient() 재사용 (없으면 내부에서 404 raise)
  2. 차트 넘버 중복 검사 (chart_number UNIQUE) — 중복 시 409
  3. 이미지 검증 — 형식(jpg/png 외 422), 크기(10MB 초과 413)
  4. X-Ray 이미지를 서버 로컬 저장소(media/xray/)에 비동기 저장
     (확장자는 Content-Type 기준으로 결정하여 형식-확장자 불일치 방지)
  5. medical_records + xray_images 두 테이블에 INSERT 후 commit
     - 동시 요청으로 인한 IntegrityError(chart_number UNIQUE 위반)는 409 처리
     - 실패 시 rollback + 저장한 파일 삭제
"""
import uuid
from datetime import datetime
from pathlib import Path

import anyio
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.medical_record import MedicalRecord
from app.repositories import medical_record_repository
# A(환자 담당)의 서비스 함수 재사용 — 인터페이스 계약 항목이므로 직접 쿼리하지 않는다
from app.services.patient_service import get_patient

# C의 환자 삭제 로직이 media/ 폴더 기준으로 X-Ray 파일을 삭제하므로 경로를 통일한다.
MEDIA_DIR = Path("media") / "xray"

# Content-Type 기준으로 저장 확장자를 결정 -> 업로드 파일명과 무관하게 형식-확장자 일치 보장
CONTENT_TYPE_EXTENSIONS = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
}

# 업로드 파일 크기 제한 (10MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


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

    # 2. 차트 넘버 중복 검사 (UNIQUE 제약) — 사전 검사
    existing = await medical_record_repository.get_medical_record_by_chart_number(
        db, chart_number
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Chart number '{chart_number}' already exists",
        )

    # 3-1. 이미지 형식 검증 (Content-Type 기준)
    extension = CONTENT_TYPE_EXTENSIONS.get(xray_image.content_type or "")
    if extension is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="X-Ray image must be a jpg or png file",
        )

    # 3-2. 파일 크기 검증 (10MB 초과 시 413)
    content = await xray_image.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="X-Ray image must be 10MB or smaller",
        )

    # 4. 이미지 로컬 저장 — 비동기(스레드 위임)로 이벤트 루프 블로킹 방지 (NFR-MDR-001)
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)
    filename = f"{patient_id}_{uuid.uuid4().hex}{extension}"
    save_path = MEDIA_DIR / filename
    await anyio.to_thread.run_sync(save_path.write_bytes, content)

    # 5. 두 테이블 INSERT — 하나의 트랜잭션으로 묶고 commit은 Service 책임
    #    shooting_datetime 은 NOT NULL 컬럼: 입력이 없으면 등록 시각으로 대체
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
    except IntegrityError:
        # 동시 요청이 사전 중복 검사를 통과해도 UNIQUE 제약에서 걸리는 경우 -> 409
        await db.rollback()
        save_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Chart number '{chart_number}' already exists",
        )
    except Exception:
        await db.rollback()
        save_path.unlink(missing_ok=True)  # DB 실패 시 고아 파일 정리
        raise

    # server_default(created_at) 값 로드 및 응답 조립
    await db.refresh(record)
    record.xray_image = image  # 응답 스키마(MedicalRecordDetailResponse)용 임시 속성
    return record
