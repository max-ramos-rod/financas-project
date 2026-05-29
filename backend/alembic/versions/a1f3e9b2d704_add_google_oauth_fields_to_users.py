"""add google oauth fields to users

Revision ID: a1f3e9b2d704
Revises: c3f1b2a9d401
Create Date: 2026-05-26 00:00:00.000000

"""
import sqlalchemy as sa

from alembic import op

revision = "a1f3e9b2d704"
down_revision = "c3f1b2a9d401"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.add_column(sa.Column("google_id", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("avatar_url", sa.String(), nullable=True))
        batch_op.alter_column("hashed_password", existing_type=sa.String(), nullable=True)

    op.create_index(op.f("ix_users_google_id"), "users", ["google_id"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_google_id"), table_name="users")

    with op.batch_alter_table("users", schema=None) as batch_op:
        batch_op.drop_column("avatar_url")
        batch_op.drop_column("google_id")
        batch_op.alter_column("hashed_password", existing_type=sa.String(), nullable=False)
