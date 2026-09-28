"""create users table and link to research and documents

Revision ID: 5efa2a364379
Revises: b7c8d9e0f1a2
Create Date: 2026-09-26 01:06:21.224044

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '5efa2a364379'
down_revision: Union[str, Sequence[str], None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password", sa.String(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=True),
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
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.add_column('documents', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_documents_user_id'), 'documents', ['user_id'], unique=False)
    op.create_foreign_key('fk_documents_user_id_users', 'documents', 'users', ['user_id'], ['id'], ondelete='CASCADE')
    op.add_column('research', sa.Column('user_id', sa.Integer(), nullable=False))
    op.create_index(op.f('ix_research_user_id'), 'research', ['user_id'], unique=False)
    op.create_foreign_key('fk_research_user_id_users', 'research', 'users', ['user_id'], ['id'], ondelete='CASCADE')


def downgrade() -> None:
    op.drop_constraint('fk_research_user_id_users', 'research', type_='foreignkey')
    op.drop_index(op.f('ix_research_user_id'), table_name='research')
    op.drop_column('research', 'user_id')
    op.drop_constraint('fk_documents_user_id_users', 'documents', type_='foreignkey')
    op.drop_index(op.f('ix_documents_user_id'), table_name='documents')
    op.drop_column('documents', 'user_id')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
