"""fix document embedding dimension

Revision ID: c5ec45a97157
Revises: e5f6a7b8c9d0
Create Date: 2026-09-22 16:32:03.638624

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect
from pgvector.sqlalchemy import VECTOR

# revision identifiers, used by Alembic.
revision: str = 'c5ec45a97157'
down_revision: Union[str, Sequence[str], None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Keep existing document chunks and embeddings while changing vector size."""
    bind = op.get_bind()
    columns = {column["name"]: column for column in inspect(bind).get_columns("documents")}
    embedding = columns.get("embedding")

    if embedding is None:
        raise RuntimeError("The documents table is missing its embedding column.")

    dimension = getattr(embedding["type"], "dim", None)
    if dimension == 384:
        return
    if dimension != 1536:
        raise RuntimeError(f"Unexpected documents.embedding dimension: {dimension!r}.")
    if "embedding_1536" in columns:
        raise RuntimeError("Cannot preserve the old embedding: embedding_1536 already exists.")

    op.alter_column("documents", "embedding", new_column_name="embedding_1536")
    op.add_column("documents", sa.Column("embedding", VECTOR(384), nullable=True))


def downgrade() -> None:
    """Restore the original vector column without discarding its values."""
    bind = op.get_bind()
    columns = {column["name"] for column in inspect(bind).get_columns("documents")}
    if "embedding_1536" not in columns:
        return

    op.drop_column("documents", "embedding")
    op.alter_column("documents", "embedding_1536", new_column_name="embedding")
