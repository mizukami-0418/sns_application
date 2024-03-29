"""add UserConect

Revision ID: 21be14a1e621
Revises: d489ae547a4e
Create Date: 2024-02-03 14:00:12.976652

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '21be14a1e621'
down_revision = 'd489ae547a4e'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_connects',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('from_user_id', sa.Integer(), nullable=True),
    sa.Column('to_user_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Integer(), nullable=True),
    sa.Column('create_at', sa.DateTime(), nullable=True),
    sa.Column('update_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('user_connects', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_connects_from_user_id'), ['from_user_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_user_connects_to_user_id'), ['to_user_id'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('user_connects', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_connects_to_user_id'))
        batch_op.drop_index(batch_op.f('ix_user_connects_from_user_id'))

    op.drop_table('user_connects')
    # ### end Alembic commands ###
