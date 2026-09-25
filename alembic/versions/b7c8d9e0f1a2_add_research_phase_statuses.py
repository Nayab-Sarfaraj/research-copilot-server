"""add research phase statuses

Revision ID: b7c8d9e0f1a2
Revises: f6a7b8c9d0e1
Create Date: 2026-09-25

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b7c8d9e0f1a2"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'PLANNING'")
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'RESEARCHING'")
    op.execute("ALTER TYPE researchstatus ADD VALUE IF NOT EXISTS 'WRITING'")


def downgrade() -> None:
    pass