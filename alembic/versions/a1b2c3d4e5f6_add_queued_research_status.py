"""add queued research status

Revision ID: a1b2c3d4e5f6
Revises: 48a05d2171ed
Create Date: 2026-09-21

"""
from typing import Sequence, Union

from alembic import op


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "48a05d2171ed"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'QUEUED'")


def downgrade() -> None:
    pass