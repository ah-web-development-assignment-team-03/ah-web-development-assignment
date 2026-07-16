# app/models/medical_record.py
"""진료 기록(medical_records) 테이블 모델.

ERD 기준:
- patients 테이블을 참조하는 FK(patient_id) 보유
- xray_images, ai_analysis_results 테이블이 이 테이블(record_id)을 참조
"""
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base


class MedicalRecord(Base):
    __tablename__ = "medical_records"

    # PK: bigint, auto increment
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"), primary_key=True, autoincrement=True
    )

    # FK: 환자 정보 테이블 참조 (NOT NULL)
    # ERD: Ref medical_records.patient_id > patients.id [delete: cascade]
    # -> 환자 삭제 시 해당 환자의 진료 기록도 DB 차원에서 함께 삭제
    patient_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("patients.id", ondelete="CASCADE"),
        nullable=False,
        comment="환자 정보 테이블 FK",
    )

    # 환자 진료 차트 번호 (NOT NULL, UNIQUE)
    chart_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        comment="환자 진료 차트 번호",
    )

    # 환자 증상 기록 (NOT NULL)
    symptoms: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="환자 증상 기록",
    )

    # 진료 정보 등록 일시 (NOT NULL, default: current_timestamp)
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
        comment="진료 정보 등록 일시",
    )

    # 진료 정보 수정 일시 (nullable, 수정 시 자동 갱신)
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        onupdate=func.current_timestamp(),
        comment="진료 정보 수정 일시",
    )

    # --- 관계 설정 ---
    # 진료 기록 N : 1 환자
    patient: Mapped["Patient"] = relationship(back_populates="medical_records")

    # 진료 기록 1 : N X-ray 이미지 / AI 판독 결과
    # ERD 기준 두 자식 테이블 모두 record_id FK에 delete: cascade 적용
    # (자식 모델 쪽 FK에 ondelete="CASCADE" 필요)
    # 팀원이 해당 모델을 작성한 뒤, 각 모델에 back_populates="medical_record"를
    # 추가하기로 합의되면 아래 주석을 해제하세요.
    # passive_deletes=True: 삭제를 DB의 ON DELETE CASCADE에 위임
    # xray_images: Mapped[list["XrayImage"]] = relationship(
    #     back_populates="medical_record", passive_deletes=True
    # )
    # ai_analysis_results: Mapped[list["AIAnalysisResult"]] = relationship(
    #     back_populates="medical_record", passive_deletes=True
    # )
