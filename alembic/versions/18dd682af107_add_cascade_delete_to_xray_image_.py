"""add cascade delete to xray image uploader

Revision ID: 18dd682af107
Revises: ea1677d7bf47
Create Date: 2026-07-16 20:44:17.187179

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18dd682af107'
down_revision: Union[str, Sequence[str], None] = 'ea1677d7bf47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _recreate_xray_images(*, cascade_user_delete: bool) -> None:
    uploader_fk_options = {"ondelete": "CASCADE"} if cascade_user_delete else {}

    op.create_table(
        "_xray_images_new",
        sa.Column(
            "id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "record_id",
            sa.BigInteger().with_variant(sa.Integer(), "sqlite"),
            sa.ForeignKey("medical_records.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "uploader_id",
            sa.Integer(),
            sa.ForeignKey("users.id", **uploader_fk_options),
            nullable=False,
        ),
        sa.Column("image_url", sa.String(length=2048), nullable=False),
        sa.Column("shooting_datetime", sa.DateTime(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
    )

    op.execute(
        sa.text(
            """
            INSERT INTO _xray_images_new (
                id,
                record_id,
                uploader_id,
                image_url,
                shooting_datetime,
                created_at
            )
            SELECT
                id,
                record_id,
                uploader_id,
                image_url,
                shooting_datetime,
                created_at
            FROM xray_images
            """
        )
    )
    op.drop_table("xray_images")
    op.rename_table("_xray_images_new", "xray_images")


def upgrade() -> None:
    """Upgrade schema."""
    _recreate_xray_images(cascade_user_delete=True)


def downgrade() -> None:
    """Downgrade schema."""
    _recreate_xray_images(cascade_user_delete=False)
