"""adding data in workload

Revision ID: 6dedad35bed5
Revises: a9ac490ab7bb
Create Date: 2025-08-03 11:36:04.755494

"""
from alembic import op
import sqlalchemy as sa
from alembic import op
import sqlalchemy as sa
from database.model import ProjectPhase , Workload
import logging

# revision identifiers, used by Alembic.
revision = '6dedad35bed5'
down_revision = 'a9ac490ab7bb'
branch_labels = None
depends_on = None


def upgrade():
    project_phases = ProjectPhase.query.all()
    print("total project_phases : ", len(project_phases))
    for project_phase  in project_phases:    
        test = Workload.update_workload(project_phase)




def downgrade():
    pass
