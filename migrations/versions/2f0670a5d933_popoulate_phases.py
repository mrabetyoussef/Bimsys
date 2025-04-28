"""popoulate_phases

Revision ID: 2f0670a5d933
Revises: 9fabcc33a9c1
Create Date: 2025-04-28 10:53:31.376814

"""
from alembic import op
import sqlalchemy as sa
from shortuuid import uuid

# revision identifiers, used by Alembic.
revision = '2f0670a5d933'
down_revision = '9fabcc33a9c1'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text(
            'INSERT INTO phases (id, name) VALUES (:id, :name)'
        ),
        [{"name": "EP", "id": uuid()},
         {"name": "APS", "id": uuid()},
         {"name": "APD", "id": uuid()},
         {"name": "PRO", "id": uuid()}]
    )

def downgrade():
    conn = op.get_bind()
    conn.execute(
        sa.text(
            "DELETE FROM phases WHERE name IN ('EP', 'APS', 'APD', 'Démolition')"
        )
    )