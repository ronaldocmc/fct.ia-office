"""Migration connection is deliberately separate from runtime credentials."""
import os
from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url

def run():
    if context.is_offline_mode():
        raise RuntimeError("Offline migrations are not supported")
    url = make_url(os.environ["FCTIA_MIGRATION_DATABASE_URL"])
    if url.drivername != "postgresql+psycopg":
        raise ValueError("Use postgresql+psycopg for the dedicated Office database")
    if url.database != "fctia_office_runtime":
        raise ValueError("Expected dedicated database fctia_office_runtime")
    engine = create_engine(url, poolclass=pool.NullPool)
    try:
        with engine.connect() as connection:
            with connection.begin():
                connection.exec_driver_sql("CREATE SCHEMA IF NOT EXISTS office_runtime")
                connection.exec_driver_sql("REVOKE ALL ON SCHEMA office_runtime FROM PUBLIC")
                context.configure(connection=connection, version_table="alembic_version",
                                  version_table_schema="office_runtime", transactional_ddl=True)
                with context.begin_transaction():
                    context.run_migrations()
    finally:
        engine.dispose()

run()
