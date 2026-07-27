from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, SmallInteger, String, DateTime, Enum, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db.databases import Base
from app.models.enums import Gender

if TYPE_CHECKING:
    from app.models.medical_record import MedicalRecord


class Patient(Base):
    __tablename__ = "patients"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(30), nullable=False, comment="환자 성명")
    age: Mapped[int] = mapped_column(SmallInteger, nullable=False, comment="환자 나이")
    gender: Mapped[Gender | None] = mapped_column(
        Enum(Gender, name="genderenum", native_enum=False),
        nullable=True,
        comment="환자 성별",
    )
    phone: Mapped[str] = mapped_column(String(11), nullable=False, comment="환자 연락처, 국내 전화번호로 한정")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False, comment="환자 정보 등록 일시"
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime, onupdate=func.now(), nullable=True, comment="환자 정보 수정 일시"
    )

    medical_records: Mapped[list["MedicalRecord"]] = relationship(
        back_populates="patient", passive_deletes=True
    )
