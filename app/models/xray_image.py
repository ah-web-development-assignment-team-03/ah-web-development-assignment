
from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from datetime import datetime
from app.core.db.databases import Base

BIGINT_TYPE = BigInteger().with_variant(Integer, "sqlite")

class XrayImage(Base):
    __tablename__ = "xray_images"

    id: Mapped[int] = mapped_column(
        BIGINT_TYPE,
        primary_key=True,
        autoincrement=True,
    )

    # medical_records 테이블의 id 참조
    record_id: Mapped[int] = mapped_column(
        BIGINT_TYPE,
        ForeignKey("medical_records.id"),
        nullable=False,
    )

    # users 테이블의 id 참조
    uploader_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    image_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )

    shooting_datetime: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.current_timestamp(),
    )