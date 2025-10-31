import os
from logging.config import fileConfig
from sqlalchemy import create_engine, text, pool
from alembic import context

# Make Alembic accept the 'clickhouse' dialect
from alembic.ddl.impl import DefaultImpl
from alembic.ddl import impl as alembic_impl
alembic_impl._impls.setdefault('clickhouse', DefaultImpl)

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def get_url():
    return os.getenv("CLICKHOUSE_URL", config.get_main_option("sqlalchemy.url"))

def run_migrations_online():
    url = get_url()
    engine = create_engine(url, poolclass=pool.NullPool)
    with engine.connect() as connection:
        # Ensure alembic_version exists and is mutable (version_num must NOT be a key)
        # 1) Create table if it doesn't exist with ORDER BY tuple() so updates are allowed
        connection.execute(text("""
            CREATE TABLE IF NOT EXISTS alembic_version
            (
                version_num String
            )
            ENGINE = MergeTree
            ORDER BY tuple()
        """))

        # 2) If it exists with ORDER BY version_num, rebuild it to ORDER BY tuple()
        try:
            sorting_key = connection.execute(text("""
                SELECT sorting_key
                FROM system.tables
                WHERE database = currentDatabase() AND name = 'alembic_version'
            """)).scalar()
        except Exception:
            sorting_key = None

        if sorting_key and 'version_num' in sorting_key:
            # Rebuild table without key on version_num
            connection.execute(text("""
                CREATE TABLE IF NOT EXISTS alembic_version_new
                (
                    version_num String
                )
                ENGINE = MergeTree
                ORDER BY tuple()
            """))
            # Copy data if any
            connection.execute(text("""
                INSERT INTO alembic_version_new SELECT version_num FROM alembic_version
            """))
            # Atomically swap and drop old
            connection.execute(text("""
                RENAME TABLE alembic_version TO alembic_version_old, alembic_version_new TO alembic_version
            """))
            connection.execute(text("""
                DROP TABLE alembic_version_old
            """))

        context.configure(
            connection=connection,
            target_metadata=None,
            version_table='alembic_version',
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    # optional offline handler if you use it
    context.configure(
        url=get_url(),
        target_metadata=None,
        literal_binds=True,
        version_table='alembic_version',
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
