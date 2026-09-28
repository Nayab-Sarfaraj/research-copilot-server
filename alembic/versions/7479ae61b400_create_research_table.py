"""create research table

Revision ID: 7479ae61b400
Revises: 
Create Date: 2026-09-18 01:27:24.040061

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '7479ae61b400'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    research_status = postgresql.ENUM(
        "CREATED",
        "PROCESSING",
        "COMPLETED",
        "FAILED",
        name="researchstatus",
        create_type=False,
    )
    research_status.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "research",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("query", sa.String(), nullable=False),
        sa.Column("status", research_status, nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("research")
    postgresql.ENUM(name="researchstatus").drop(op.get_bind(), checkfirst=True)
