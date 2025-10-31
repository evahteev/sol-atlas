"""
create liquidity snapshots.

Revision ID: db8facaa64ba
Revises: dcc43e5b67a3
Create Date: 2024-03-22 18:34:21.671753
"""
import os
import string
from functools import cache

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'db8facaa64ba'
down_revision = 'dcc43e5b67a3'
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
        create table snapshot_liquidity
        (
            timestamp          UInt32,
            factory_address    String CODEC(ZSTD(1)),
            pool_address       String CODEC(ZSTD(1)),
            token_address      String CODEC(ZSTD(1)),
            liquidity_stable   Float64,
            liquidity_native   Float64
        )
        engine = ${replicated}MergeTree${replication_path} PARTITION BY toDate(FROM_UNIXTIME(timestamp))
        ORDER BY (token_address, factory_address, pool_address)
    """

    on_cluster = os.getenv('ON_CLUSTER', '').lower() in ('true', '1')
    if on_cluster:
        on_cluster = "ON CLUSTER '{cluster}'"
    else:
        on_cluster = ""

    replication_path = ""
    if is_clickhouse_replicated():
        on_cluster = on_cluster
        replicated = "Replicated"
        replication_path = "('/clickhouse/tables/{database}/{shard}/{table}', '{replica}-{cluster}')"
    else:
        on_cluster = ""
        replicated = ""

    sql = string.Template(schema_template).substitute(
        on_cluster=on_cluster,
        replicated=replicated,
        replication_path=replication_path,
    )
    statements = filter(None, map(str.strip, sql.split(";\n")))
    for statement in statements:
        op.execute(statement)


def downgrade() -> None:
    schema_template = "DROP TABLE snapshot_liquidity $on_cluster SYNC"

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

    op.execute(sql)
