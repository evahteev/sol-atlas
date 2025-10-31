import os
from logging.config import fileConfig
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from alembic import context
from clickhouse_sqlalchemy.alembic.dialect import include_object, patch_alembic_version
from sqlalchemy import engine_from_config, pool

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = None

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    context.configure(
        url='clickhouse+native://127.0.0.1:1',
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        patch_alembic_version(context)
        context.run_migrations()


def update_query_params(url: str, **params: str) -> str:
    url_parts = list(urlparse(url))
    query = dict(parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = urlencode(query)
    return urlunparse(url_parts)


def run_migrations_online() -> None:
    """
    Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.
    """
    url = os.getenv('CLICKHOUSE_URL')
    if url is None:
        raise SystemExit('CLICKHOUSE_URL environment variable is not set')

    # In Clickhouse Alembic uses "ALTER TABLE UPDATE" statement to update alembic_version
    # table. This causes a table mutation. By default, mutations are asynchronous
    # (mutations_sync=0). We need to make sure mutations_sync setting is set to 1 or 2 to
    # make mutations synchronous as this is crucial for migrations.

    # URL query params work only for clickhouse+native 🤷
    url = update_query_params(url, mutations_sync='2')
    # connection_args works only for clickhouse+http 🤷
    connection_args = {"ch_settings": {"mutations_sync": "2"}}

    assert isinstance(url, str)
    config.set_main_option('sqlalchemy.url', url)

    engine = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        connect_args=connection_args,
    )
    assert engine.dialect.name == 'clickhouse'

    with engine.connect() as connection:
        mutations_sync = connection.execute(
            "select value from system.settings where name = 'mutations_sync'"
        ).scalar()
        if mutations_sync not in ('1', '2'):
            raise ValueError(
                f"mutations_sync setting is {mutations_sync!r}, but should be '1' or '2'."
                f" Make sure you use native connection URL and"
                f" mutations_sync parameter is set to 1 or 2"
            )

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            include_object=include_object,
        )

        with context.begin_transaction():
            patch_alembic_version(context)
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
