# type: ignore

"""Update poll related databases

Revision ID: 58181eafb0cd
Revises: 13e77c214ff0
Create Date: 2023-01-26 22:52:02.741639

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "58181eafb0cd"
down_revision = "13e77c214ff0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("poll", sa.Column("max_answers", sa.SmallInteger(), nullable=False))
    op.add_column("poll", sa.Column("users_can_change_answer", sa.Boolean(), nullable=False))
    op.add_column("poll", sa.Column("closed", sa.Boolean(), nullable=False))
    op.add_column("poll", sa.Column("public_results", sa.Boolean(), nullable=False))

    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE polltype ADD VALUE 'BOOLEAN'")
        op.execute("ALTER TYPE polltype ADD VALUE 'OPINION'")
        op.execute("ALTER TYPE polltype ADD VALUE 'ENTRY'")
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("poll", "public_results")
    op.drop_column("poll", "closed")
    op.drop_column("poll", "users_can_change_answer")
    op.drop_column("poll", "max_answers")

    op.execute("ALTER TYPE polltype RENAME TO polltype_old")
    op.execute("CREATE TYPE polltype AS ENUM('CHOICE')")
    op.execute(("ALTER TABLE poll ALTER COLUMN type TYPE polltype USING polltype::text::polltype"))
    op.execute("DROP TYPE polltype_old")
    # ### end Alembic commands ###
