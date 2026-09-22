"""add research sources table

Revision ID: f6a7b8c9d0e1
Revises: c5ec45a97157
Create Date: 2026-09-22

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "c5ec45a97157"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    source_type = postgresql.ENUM(
        "web",
        "document",
        name="sourcetype",
        create_type=False,
    )
    source_type.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "research_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("research_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.Column("source_type", source_type, nullable=False),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.ForeignKeyConstraint(
            ["research_id"],
            ["research.id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    op.drop_table("research_sources")
    postgresql.ENUM(name="sourcetype").drop(op.get_bind(), checkfirst=True)