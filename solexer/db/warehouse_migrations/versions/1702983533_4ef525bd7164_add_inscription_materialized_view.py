"""
Add inscription materialized view.

Revision ID: 4ef525bd7164
Revises: ccb0c5dba4d4
Create Date: 2023-12-19 11:58:53.656998
"""
import os
import string
from functools import cache

from alembic import op

# revision identifiers, used by Alembic.
revision = '4ef525bd7164'
down_revision = 'ccb0c5dba4d4'
branch_labels = None
depends_on = None


@cache
def is_clickhouse_replicated():
    if os.getenv('CLICKHOUSE_REPLICATED', '').lower() in ('true', '1'):
        return True

    result = op.get_bind().execute("SELECT count() FROM system.replicas")
    if result:
        return result.one()[0] > 0

    return False


def upgrade() -> None:
    schema_template = """
        CREATE TABLE IF NOT EXISTS`inscriptions` $on_cluster
        (
            `block_number` UInt64,
            `block_timestamp` UInt32,
            `transaction_hash` String CODEC(ZSTD(1)),
            `from_address` String CODEC(ZSTD(1)),
            `to_address` Nullable(String) CODEC(ZSTD(1)),
            `transaction_index` UInt32,
            `gas_used` UInt64,
            `gas_price` UInt256,
            `standard` LowCardinality(String),
            `operation` LowCardinality(String),
            `ticker` String CODEC(ZSTD(1)),
            `amount` String CODEC(ZSTD(1)),
            `inscription` String CODEC(ZSTD(1)),
            INDEX blocks_timestamp block_timestamp TYPE minmax GRANULARITY 1
        )
        ENGINE = ${replicated}ReplacingMergeTree${replication_path}
        ORDER BY (block_number, transaction_hash)
        SETTINGS index_granularity = 8192;
        
        
        
        CREATE MATERIALIZED VIEW `inscription_mv_parsed_transactions` $on_cluster
        TO `inscriptions`
        (
            `block_number` UInt64,
            `block_timestamp` UInt32,
            `transaction_hash` String,
            `from_address` String,
            `to_address` Nullable(String),
            `transaction_index` UInt32,
            `standard` LowCardinality(String),
            `operation` LowCardinality(String),
            `ticker` String,
            `amount` String,
            `gas_used` UInt64,
            `gas_price` UInt256,
            `inscription` String
        ) AS
        SELECT
            block_number AS block_number,
            block_timestamp AS block_timestamp,
            hash AS transaction_hash,
            from_address AS from_address,
            to_address AS to_address,
            transaction_index AS transaction_index,
            ifNull(receipt_gas_used, 0) AS gas_used,
            ifNull(receipt_effective_gas_price, 0) AS gas_price,
            JSONExtractString(input_json, 'p') AS standard,
            JSONExtractString(input_json, 'op') AS operation,
            JSONExtractString(inscription, 'tick') AS ticker,
            JSONExtractInt(inscription, 'amt') AS amount,
            input_json AS inscription
        FROM
        (
            SELECT 
                block_number,
                block_timestamp,
                hash,
                from_address,
                to_address,
                transaction_index,
                receipt_gas_used,
                receipt_effective_gas_price,
                substring(unhexed_input, position(unhexed_input, '{')) AS input_json, -- Extracts the JSON part from the input
                unhex(input) AS unhexed_input -- Converts hex input to binary string
            FROM transactions
        )
        WHERE
            JSONHas(input_json, 'p') AND
            JSONHas(input_json, 'op'); -- Check if JSON extraction is successful
    """

    if is_clickhouse_replicated():
        on_cluster = "ON CLUSTER 'stage_testnets'"
        replicated = "Replicated"
        replication_path = "('/clickhouse/tables/{database}/{shard}/{table}', '{replica}-{cluster}')"
    else:
        on_cluster = ""
        replicated = ""
        replication_path = ""
    sql = string.Template(schema_template).substitute(
        on_cluster=on_cluster,
        replicated=replicated,
        replication_path=replication_path,
    )
    statements = filter(None, map(str.strip, sql.split(";\n")))
    for statement in statements:
        print(statement)
        # op.execute(statement)


def downgrade() -> None:
    schema_template = "DROP TABLE example $on_cluster SYNC"

    if is_clickhouse_replicated():
        on_cluster = "ON CLUSTER 'stage_testnets'",
        replicated = "Replicated"
        replication_path = "('/clickhouse/tables/{database}/{shard}/{table}', '{replica}-{cluster}')"

    else:
        on_cluster = ""
        replicated = ""
        replication_path = ""
    _ = replicated

    sql = string.Template(schema_template).substitute(
        on_cluster=on_cluster,
        replicated=replicated,
        replication_path=replication_path,
    )

    op.execute(sql)
