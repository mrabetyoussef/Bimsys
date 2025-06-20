"""Add assigned_user to project_phase

Revision ID: 259f4e91102b
Revises: 0cc7b99d54e3
Create Date: 2025-06-09 16:41:20.780128

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '259f4e91102b'
down_revision = '0cc7b99d54e3'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    # op.drop_table('_alembic_tmp_phases')
    # with op.batch_alter_table('phases', schema=None) as batch_op:
    #     batch_op.drop_constraint(None, type_='foreignkey')
    #     batch_op.drop_column('project_id')

    with op.batch_alter_table('project_phases', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assigned_bimuser_id', sa.String(length=16), nullable=True))
        batch_op.create_foreign_key('fk_projectphase_user', 'BimUsers', ['assigned_bimuser_id'], ['id'])

    # with op.batch_alter_table('tasks', schema=None) as batch_op:
    #     batch_op.create_foreign_key(None, 'project_phases', ['project_phase_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('tasks', schema=None) as batch_op:
        batch_op.drop_constraint(None, type_='foreignkey')

    with op.batch_alter_table('project_phases', schema=None) as batch_op:
        batch_op.drop_constraint('fk_projectphase_user', type_='foreignkey')
        batch_op.drop_column('assigned_bimuser_id')

    with op.batch_alter_table('phases', schema=None) as batch_op:
        batch_op.add_column(sa.Column('project_id', sa.VARCHAR(), nullable=True))
        batch_op.create_foreign_key(None, 'projects', ['project_id'], ['id'])

    op.create_table('_alembic_tmp_phases',
    sa.Column('id', sa.VARCHAR(length=16), nullable=False),
    sa.Column('name', sa.VARCHAR(length=255), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('id')
    )
    # ### end Alembic commands ###
