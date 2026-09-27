"""add video processing fields

Revision ID: ca9ed1f69a2d
Revises: ca198b0181eb
Create Date: 2026-09-27 14:03:25.715936
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "ca9ed1f69a2d"
down_revision: Union[str, Sequence[str], None] = "ca198b0181eb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "videos",
        sa.Column(
            "processing_status",
            sa.String(length=50),
            nullable=False,
            server_default="pending",
        ),
    )

    op.add_column(
        "videos",
        sa.Column(
            "transcript",
            sa.Text(),
            nullable=True,
        ),
    )

    op.add_column(
        "videos",
        sa.Column(
            "processing_error",
            sa.Text(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("videos", "processing_error")
    op.drop_column("videos", "transcript")
    op.drop_column("videos", "processing_status")