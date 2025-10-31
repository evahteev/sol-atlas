"""
add reserves in trades.

Revision ID: 3799feafd328
Revises: 724414794765
Create Date: 2024-01-23 14:17:47.027430
"""
import os
import string
from functools import cache

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '3799feafd328'
down_revision = '724414794765'
branch_labels = None
depends_on = None


@cache
def is_clickhouse_replicated():
    if os.getenv('CLICKHOUSE_REPLICATED', '').lower() in ('true', '1'):
        return True

    result = op.get_bind().execute(text("SELECT count() FROM system.replicas"))
    if result:
        return result.one()[0] > 0

    return False


def upgrade() -> None:
    schema_template = """
    ALTER TABLE dex_trades $on_cluster ADD COLUMN reserves Array(Float64) DEFAULT [] CODEC(ZSTD(1)) AFTER pool_address;
    ALTER TABLE dex_trades $on_cluster ADD COLUMN reserves_stable Array(Float64) DEFAULT [] CODEC(ZSTD(1)) AFTER reserves;
    ALTER TABLE dex_trades $on_cluster ADD COLUMN reserves_native Array(Float64) DEFAULT [] CODEC(ZSTD(1)) AFTER reserves_stable;
    ALTER TABLE dex_trades $on_cluster ADD COLUMN lp_token_address String DEFAULT '' CODEC(ZSTD(1)) AFTER pool_address;
    """

    on_cluster = os.getenv('ON_CLUSTER', '').lower() in ('true', '1')
    if on_cluster:
        on_cluster = "ON CLUSTER '{cluster}'"
    else:
        on_cluster = ""

    if is_clickhouse_replicated():
        on_cluster = on_cluster
        replicated = "Replicated"
    else:
        on_cluster = ""
        replicated = ""

    sql = string.Template(schema_template).substitute(
        on_cluster=on_cluster,
        replicated=replicated,
    )
    statements = filter(None, map(str.strip, sql.split(";\n")))
    for statement in statements:
        op.execute(statement)


def downgrade() -> None:
    schema_template = """
        ALTER TABLE dex_trades $on_cluster DROP COLUMN reserves;
        ALTER TABLE dex_trades $on_cluster DROP COLUMN reserves_stable;
        ALTER TABLE dex_trades $on_cluster DROP COLUMN reserves_native;
        ALTER TABLE dex_trades $on_cluster DROP COLUMN lp_token_address;
    """

    on_cluster = os.getenv('ON_CLUSTER', '').lower() in ('true', '1')
    if on_cluster:
        on_cluster = "ON CLUSTER '{cluster}'"
    else:
        on_cluster = ""

    if is_clickhouse_replicated():
        on_cluster = on_cluster
        replicated = "Replicated"
    else:
        on_cluster = ""
        replicated = ""

    _ = replicated

    sql = string.Template(schema_template).substitute(
        on_cluster=on_cluster,
    )

    statements = filter(None, map(str.strip, sql.split(";\n")))
    for statement in statements:
        op.execute(statement)
