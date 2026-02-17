"""add settlement fields to transacoes

Revision ID: 2c1f9e8a6d44
Revises: 4b9c2f6d1a77
Create Date: 2026-02-12 23:20:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "2c1f9e8a6d44"
down_revision = "4b9c2f6d1a77"
branch_labels = None
depends_on = None


def upgrade() -> None:
    statusliquidacao = sa.Enum("PREVISTO", "LIQUIDADO", "ATRASADO", "CANCELADO", name="statusliquidacao")
    statusliquidacao.create(op.get_bind(), checkfirst=True)

    op.add_column("transacoes", sa.Column("data_vencimento", sa.Date(), nullable=True))
    op.add_column("transacoes", sa.Column("data_liquidacao", sa.Date(), nullable=True))
    op.add_column("transacoes", sa.Column("status_liquidacao", statusliquidacao, nullable=True))
    op.add_column("transacoes", sa.Column("valor_multa", sa.Float(), nullable=False, server_default="0"))
    op.add_column("transacoes", sa.Column("valor_juros", sa.Float(), nullable=False, server_default="0"))
    op.add_column("transacoes", sa.Column("valor_desconto", sa.Float(), nullable=False, server_default="0"))

    op.execute("UPDATE transacoes SET status_liquidacao = 'LIQUIDADO' WHERE status_liquidacao IS NULL")
    op.alter_column("transacoes", "status_liquidacao", nullable=False)
    op.alter_column("transacoes", "valor_multa", server_default=None)
    op.alter_column("transacoes", "valor_juros", server_default=None)
    op.alter_column("transacoes", "valor_desconto", server_default=None)


def downgrade() -> None:
    op.drop_column("transacoes", "valor_desconto")
    op.drop_column("transacoes", "valor_juros")
    op.drop_column("transacoes", "valor_multa")
    op.drop_column("transacoes", "status_liquidacao")
    op.drop_column("transacoes", "data_liquidacao")
    op.drop_column("transacoes", "data_vencimento")
    sa.Enum(name="statusliquidacao").drop(op.get_bind(), checkfirst=True)
