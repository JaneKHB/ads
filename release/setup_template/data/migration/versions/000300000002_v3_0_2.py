"""v3.0.2

Revision ID: 000300000002
Revises:
Create Date: 2023-06-22

"""
from alembic import op
import sqlalchemy as sa
from migration import migration


# revision identifiers, used by Alembic.
revision = '000300000002'
down_revision = '000300000001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    migration.upgrade(revision)
    print(f"Upgrade from {down_revision} to {revision} finish.")



def downgrade() -> None:
    migration.downgrade(revision)
    print(f"Downgrade from {revision} to {down_revision} finish.")
