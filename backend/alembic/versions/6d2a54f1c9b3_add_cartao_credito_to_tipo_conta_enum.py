"""add cartao_credito to tipo conta enum

Revision ID: 6d2a54f1c9b3
Revises: 2c1f9e8a6d44
Create Date: 2026-02-13 12:20:00.000000

"""
from alembic import op


revision = "6d2a54f1c9b3"
down_revision = "2c1f9e8a6d44"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE tipoconta ADD VALUE IF NOT EXISTS 'CARTAO_CREDITO'")


def downgrade() -> None:
    # PostgreSQL nao permite remover valor de ENUM com seguranca sem recriar o tipo.
    pass
