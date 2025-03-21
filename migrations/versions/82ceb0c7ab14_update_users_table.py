"""update users table

Revision ID: 82ceb0c7ab14
Revises: 
Create Date: 2025-03-20 19:12:11.086277

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '82ceb0c7ab14'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('BimUsers', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               type_=sa.String(length=16),
               existing_nullable=False)

    with op.batch_alter_table('Task', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.INTEGER(),
               type_=sa.String(length=16),
               existing_nullable=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('Task', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.String(length=16),
               type_=sa.INTEGER(),
               existing_nullable=False)

    with op.batch_alter_table('BimUsers', schema=None) as batch_op:
        batch_op.alter_column('id',
               existing_type=sa.String(length=16),
               type_=sa.INTEGER(),
               existing_nullable=False)

    # ### end Alembic commands ###
