"""add delegacoes table

Revision ID: 7a4a9f2c1b10
Revises: 9804a6a833db
Create Date: 2026-02-12 17:40:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "7a4a9f2c1b10"
down_revision = "9804a6a833db"
branch_labels = None
depends_on = None


def upgrade() -> None:
    delegacaostatus = sa.Enum("PENDING", "ACTIVE", "REVOKED", name="delegacaostatus")

    op.create_table(
        "delegacoes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("owner_user_id", sa.Integer(), nullable=False),
        sa.Column("delegate_user_id", sa.Integer(), nullable=False),
        sa.Column("status", delegacaostatus, nullable=False),
        sa.Column("can_write", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["delegate_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["owner_user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("owner_user_id", "delegate_user_id", name="uq_delegacoes_owner_delegate"),
    )
    op.create_index(op.f("ix_delegacoes_id"), "delegacoes", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_delegacoes_id"), table_name="delegacoes")
    op.drop_table("delegacoes")
    sa.Enum(name="delegacaostatus").drop(op.get_bind(), checkfirst=True)
