from decimal import Decimal

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db.databases import Base
from app.core.db.models import TimestampMixin


class AIAnalysisResult(TimestampMixin, Base):
    __tablename__ = "ai_analysis_results"
    __table_args__ = (
        UniqueConstraint("record_id", "ai_model", name="uq_ai_analysis_results_record_model"),
    )

    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    record_id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        ForeignKey("medical_records.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_pneumonia: Mapped[bool] = mapped_column(Boolean, nullable=False)
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    heatmap_url: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ai_model: Mapped[str] = mapped_column(String(50), nullable=False)
