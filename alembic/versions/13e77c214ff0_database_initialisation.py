"""database_initialisation

Revision ID: 13e77c214ff0
Revises: 
Create Date: 2023-01-11 21:06:29.090289

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '13e77c214ff0'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('guild',
    sa.Column('guild_id', sa.BigInteger(), nullable=False),
    sa.Column('premium_type', sa.Enum('NONE', name='premiumtype'), nullable=False),
    sa.Column('translations_are_public', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('guild_id')
    )
    op.create_table('user',
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_table('poll',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('message_id', sa.BigInteger(), nullable=False),
    sa.Column('channel_id', sa.BigInteger(), nullable=False),
    sa.Column('guild_id', sa.BigInteger(), nullable=False),
    sa.Column('author_id', sa.BigInteger(), nullable=False),
    sa.Column('type', sa.Enum('CHOICE', name='polltype'), nullable=False),
    sa.Column('multiple', sa.Boolean(), nullable=False),
    sa.Column('label', sa.String(), nullable=False),
    sa.Column('creation_date', sa.Date(), nullable=False),
    sa.Column('end_date', sa.Date(), nullable=True),
    sa.ForeignKeyConstraint(['guild_id'], ['guild.guild_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('usage',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('type', sa.Enum('SLASHCOMMAND', name='usagetype'), nullable=False),
    sa.Column('details', sa.String(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.Column('guild_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['guild_id'], ['guild.guild_id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.user_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('poll_answer',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('poll_id', sa.Integer(), nullable=False),
    sa.Column('value', sa.String(), nullable=False),
    sa.Column('user_id', sa.BigInteger(), nullable=False),
    sa.ForeignKeyConstraint(['poll_id'], ['poll.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('poll_choice',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('poll_id', sa.Integer(), nullable=False),
    sa.Column('label', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['poll_id'], ['poll.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('poll_choice')
    op.drop_table('poll_answer')
    op.drop_table('usage')
    op.drop_table('poll')
    op.drop_table('user')
    op.drop_table('guild')
    # ### end Alembic commands ###
