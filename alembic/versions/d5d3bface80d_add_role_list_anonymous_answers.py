# type: ignore

"""Add role list & anonymous answers

Revision ID: d5d3bface80d
Revises: b9b8f970b67f
Create Date: 2023-03-07 20:41:08.117604

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "d5d3bface80d"
down_revision = "b9b8f970b67f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("poll", sa.Column("anonymous_allowed", sa.Boolean(), nullable=True))
    op.add_column("poll", sa.Column("allowed_roles", sa.ARRAY(sa.BigInteger()), nullable=True))
    op.add_column("poll_answer", sa.Column("anonymous", sa.Boolean(), nullable=True))

    op.execute("UPDATE poll SET anonymous_allowed = false")
    op.execute("UPDATE poll SET allowed_roles = '{}'")
    op.execute("UPDATE poll_answer SET anonymous = false")

    op.alter_column("poll", "anonymous_allowed", nullable=False)
    op.alter_column("poll", "allowed_roles", nullable=False)
    op.alter_column("poll_answer", "anonymous", nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("poll_answer", "anonymous")
    op.drop_column("poll", "allowed_roles")
    op.drop_column("poll", "anonymous_allowed")
    # ### end Alembic commands ###
