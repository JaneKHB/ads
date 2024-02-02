"""v3.0.7

Revision ID: 000300000007
Revises:
Create Date: 2023-07-26

"""
from alembic import op
import sqlalchemy as sa
from migration import migration


# revision identifiers, used by Alembic.
revision = '000300000007'
down_revision = '000300000006'
branch_labels = None
depends_on = None


def upgrade() -> None:
    migration.upgrade(revision)
    print(f"Upgrade from {down_revision} to {revision} finish.")



def downgrade() -> None:
    migration.downgrade(revision)
    print(f"Downgrade from {revision} to {down_revision} finish.")
