"""v3.0.1

Revision ID: 000300000001
Revises:
Create Date: 2023-06-14

"""
from alembic import op
import sqlalchemy as sa
from migration import migration


# revision identifiers, used by Alembic.
revision = '000300000001'
down_revision = '000300000000'
branch_labels = None
depends_on = None


def upgrade() -> None:
    migration.upgrade(revision)
    print(f"Upgrade from {down_revision} to {revision} finish.")



def downgrade() -> None:
    migration.downgrade(revision)
    print(f"Downgrade from {revision} to {down_revision} finish.")
