"""add conta cartao ciclos table

Revision ID: c3f1b2a9d401
Revises: b0e2d5a8c4f1
Create Date: 2026-04-04 13:15:00.000000
"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "c3f1b2a9d401"
down_revision = "b0e2d5a8c4f1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conta_cartao_ciclos",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("conta_id", sa.Integer(), sa.ForeignKey("contas.id"), nullable=False),
        sa.Column("competencia_ano", sa.Integer(), nullable=False),
        sa.Column("competencia_mes", sa.Integer(), nullable=False),
        sa.Column("data_fechamento_prevista", sa.Date(), nullable=False),
        sa.Column("data_fechamento_real", sa.Date(), nullable=True),
        sa.Column("data_vencimento_prevista", sa.Date(), nullable=False),
        sa.Column("data_vencimento_real", sa.Date(), nullable=True),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("conta_id", "competencia_ano", "competencia_mes", name="uq_conta_cartao_ciclo_competencia"),
    )
    op.create_index(op.f("ix_conta_cartao_ciclos_id"), "conta_cartao_ciclos", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_conta_cartao_ciclos_id"), table_name="conta_cartao_ciclos")
    op.drop_table("conta_cartao_ciclos")
