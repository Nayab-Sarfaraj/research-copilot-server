"""add research reports

Revision ID: 48a05d2171ed
Revises: 7479ae61b400
Create Date: 2026-09-18 23:21:24.765343

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '48a05d2171ed'
down_revision: Union[str, Sequence[str], None] = '7479ae61b400'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "research_reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("content", sa.String(), nullable=False),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("research_id", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(["research_id"], ["research.id"]),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("research_reports")
