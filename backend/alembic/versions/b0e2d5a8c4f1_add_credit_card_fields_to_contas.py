"""add credit card fields to contas

Revision ID: b0e2d5a8c4f1
Revises: 6d2a54f1c9b3
Create Date: 2026-02-13 13:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "b0e2d5a8c4f1"
down_revision = "6d2a54f1c9b3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("contas", sa.Column("dia_fechamento", sa.Integer(), nullable=True))
    op.add_column("contas", sa.Column("dia_vencimento", sa.Integer(), nullable=True))
    op.add_column("contas", sa.Column("limite_credito", sa.Float(), nullable=True))


def downgrade() -> None:
    op.drop_column("contas", "limite_credito")
    op.drop_column("contas", "dia_vencimento")
    op.drop_column("contas", "dia_fechamento")
