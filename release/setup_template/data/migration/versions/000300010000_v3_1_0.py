"""v3.1.0

Revision ID: 000300010000_v3_1_0
Revises:
Create Date: 2023-12-20

"""
from alembic import op
import sqlalchemy as sa
from migration import migration


# revision identifiers, used by Alembic.
revision = '000300010000'
down_revision = '00030000000B'
branch_labels = None
depends_on = None


def column_type_change():
    from sqlalchemy import create_engine, MetaData
    from sqlalchemy.dialects.postgresql import TIMESTAMP
    from sqlalchemy.sql import text

    # PostgreSQL
    DB_CONNECTION_STRING = 'postgresql://rssadmin:canon@localhost:5443/rssdb'

    # Engine
    engine = create_engine(DB_CONNECTION_STRING)

    # get schema
    metadata = MetaData()
    metadata.reflect(bind=engine, schema='cras_db')

    # SHOW TIMEZONE 
    with engine.connect() as connection:
        result = connection.execute(text("SHOW TIMEZONE"))
        timezone_result = result.scalar()

    if "'" not in timezone_result:
        timezone_result = "'" + timezone_result + "'"

    print(f"Database timezone is {timezone_result}.")

    # change table column type
    for table_name, table in metadata.tables.items():
        alter_column_queries = []
        for column in table.columns:
            if isinstance(column.type, TIMESTAMP):
                if column.type.timezone is False:
                    alter_query = f"ALTER TABLE {table_name} ALTER COLUMN {column.name} TYPE timestamptz using {column.name} at time zone {timezone_result}"
                    alter_column_queries.append(alter_query)

        # execute query
        if len(alter_column_queries):
            with engine.connect() as connection:
                for query in alter_column_queries:
                    connection.execute(text(query))
            print(f"table = {table_name} column type changed.")


def upgrade() -> None:
    try:
        column_type_change()
    except Exception as ex:
        print(f"Upgrade fail. {str(ex)}.")
        raise ex
    else:
        migration.upgrade(revision)
        print(f"Upgrade from {down_revision} to {revision} finish.")


def downgrade() -> None:
    migration.downgrade(revision)
    print(f"Downgrade from {revision} to {down_revision} finish.")
