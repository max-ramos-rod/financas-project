"""add invitation fields to delegacoes

Revision ID: 4b9c2f6d1a77
Revises: 7a4a9f2c1b10
Create Date: 2026-02-12 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = "4b9c2f6d1a77"
down_revision = "7a4a9f2c1b10"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("delegacoes", "delegate_user_id", existing_type=sa.Integer(), nullable=True)
    op.add_column("delegacoes", sa.Column("invited_email", sa.String(length=255), nullable=True))
    op.add_column("delegacoes", sa.Column("invite_token", sa.String(length=128), nullable=True))
    op.add_column("delegacoes", sa.Column("invite_expires_at", sa.DateTime(timezone=True), nullable=True))

    op.execute(
        """
        UPDATE delegacoes d
        SET invited_email = u.email
        FROM users u
        WHERE d.delegate_user_id = u.id
        """
    )

    op.alter_column("delegacoes", "invited_email", existing_type=sa.String(length=255), nullable=False)
    op.create_index(op.f("ix_delegacoes_invited_email"), "delegacoes", ["invited_email"], unique=False)
    op.create_index(op.f("ix_delegacoes_invite_token"), "delegacoes", ["invite_token"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_delegacoes_invite_token"), table_name="delegacoes")
    op.drop_index(op.f("ix_delegacoes_invited_email"), table_name="delegacoes")
    op.drop_column("delegacoes", "invite_expires_at")
    op.drop_column("delegacoes", "invite_token")
    op.drop_column("delegacoes", "invited_email")
    op.alter_column("delegacoes", "delegate_user_id", existing_type=sa.Integer(), nullable=False)
