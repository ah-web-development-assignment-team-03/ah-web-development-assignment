"""update ai_analysis_results: heatmap_url nullable, unique(record_id, ai_model)

Revision ID: b7c3d1e2f4a0
Revises: 18dd682af107
Create Date: 2026-07-21 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b7c3d1e2f4a0'
down_revision: Union[str, Sequence[str], None] = '18dd682af107'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

BIGINT = sa.BigInteger().with_variant(sa.Integer(), "sqlite")


def _recreate_ai_analysis_results(*, heatmap_nullable: bool, unique_record_model: bool) -> None:
    constraints = [
        sa.ForeignKeyConstraint(["record_id"], ["medical_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    ]
    if unique_record_model:
        constraints.append(
            sa.UniqueConstraint("record_id", "ai_model", name="uq_ai_analysis_results_record_model")
        )

    op.create_table(
        "_ai_analysis_results_new",
        sa.Column("id", BIGINT, autoincrement=True, nullable=False),
        sa.Column("record_id", BIGINT, nullable=False),
        sa.Column("is_pneumonia", sa.Boolean(), nullable=False),
        sa.Column("confidence", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("heatmap_url", sa.String(length=255), nullable=heatmap_nullable),
        sa.Column("ai_model", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("(CURRENT_TIMESTAMP)"), nullable=True),
        *constraints,
    )

    # downgrade 시 heatmap_url=NULL 행이 존재하면 NOT NULL 컬럼으로 복사할 수 없으므로
    # 빈 문자열로 대체한다.
    heatmap_expr = "heatmap_url" if heatmap_nullable else "COALESCE(heatmap_url, '')"

    op.execute(
        sa.text(
            f"""
            INSERT INTO _ai_analysis_results_new (
                id, record_id, is_pneumonia, confidence,
                heatmap_url, ai_model, created_at, updated_at
            )
            SELECT
                id, record_id, is_pneumonia, confidence,
                {heatmap_expr}, ai_model, created_at, updated_at
            FROM ai_analysis_results
            """
        )
    )

    op.drop_index(op.f("ix_ai_analysis_results_record_id"), table_name="ai_analysis_results")
    op.drop_table("ai_analysis_results")
    op.rename_table("_ai_analysis_results_new", "ai_analysis_results")
    op.create_index(
        op.f("ix_ai_analysis_results_record_id"),
        "ai_analysis_results",
        ["record_id"],
        unique=False,
    )


def upgrade() -> None:
    _recreate_ai_analysis_results(heatmap_nullable=True, unique_record_model=True)


def downgrade() -> None:
    _recreate_ai_analysis_results(heatmap_nullable=False, unique_record_model=False)
