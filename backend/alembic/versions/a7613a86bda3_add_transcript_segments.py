"""add transcript segments

Revision ID: add_transcript_segments
Revises: ca9ed1f69a2d
Create Date: 2026-09-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "add_transcript_segments"
down_revision: Union[str, Sequence[str], None] = "ca9ed1f69a2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "videos",
        sa.Column(
            "transcript_segments",
            sa.JSON(),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("videos", "transcript_segments")