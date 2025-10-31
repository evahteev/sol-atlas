"""
add pools count table.

Revision ID: e63032f915ee
Revises: db8facaa64ba
Create Date: 2024-03-27 22:16:34.611230
"""

import os
import string
from functools import cache

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'e63032f915ee'
down_revision = 'db8facaa64ba'
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
    create table pools_counts $on_cluster
    (
        token_address String,
        pools_count AggregateFunction(uniq, Nullable(String))
    )
    engine = AggregatingMergeTree ORDER BY token_address
        SETTINGS index_granularity = 8192;
    
    CREATE MATERIALIZED VIEW pools_counts_mv TO pools_counts
    (
        `token_address` String,
        `pools_count` AggregateFunction(uniq, Nullable(String))
    ) AS
    SELECT
        token_address,
        uniqState(toNullable(concat(pool_address, token_address))) AS pools_count
    FROM (
        SELECT address as pool_address,
               arrayJoin(token_addresses) as token_address
        FROM dex_pools
     )
    GROUP BY token_address;
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
        DROP TABLE pools_counts $on_cluster;
        DROP VIEW pools_counts_mv $on_cluster
    """

    if is_clickhouse_replicated():
        on_cluster = "ON CLUSTER '{cluster}'"
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
