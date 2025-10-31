"""
Init.

Revision ID: ccb0c5dba4d4
Revises:
Create Date: 2023-07-31 17:30:50.941585
"""
import os
import string

from alembic import op

# revision identifiers, used by Alembic.
revision = 'ccb0c5dba4d4'
down_revision = None
branch_labels = None
depends_on = None

SCHEMA_TEMPLATE = """
CREATE TABLE IF NOT EXISTS `blocks` $on_cluster
(
    `number` UInt64 CODEC(Delta(8), LZ4),
    `hash` String CODEC(ZSTD(1)),
    `parent_hash` String CODEC(ZSTD(1)),
    `nonce` Nullable(String) CODEC(ZSTD(1)),
    `sha3_uncles` String CODEC(ZSTD(1)),
    `logs_bloom` String CODEC(ZSTD(1)),
    `transactions_root` String CODEC(ZSTD(1)),
    `state_root` String CODEC(ZSTD(1)),
    `receipts_root` String CODEC(ZSTD(1)),
    `miner` String CODEC(ZSTD(1)),
    `difficulty` UInt256,
    `total_difficulty` UInt256,
    `size` UInt64,
    `extra_data` String CODEC(ZSTD(1)),
    `gas_limit` UInt64,
    `gas_used` UInt64,
    `timestamp` UInt32,
    `transaction_count` UInt64,
    `base_fee_per_gas` Nullable(Int64),
    `is_reorged` Bool DEFAULT 0,
    INDEX blocks_timestamp timestamp TYPE minmax GRANULARITY 1
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (number, hash)
SETTINGS index_granularity = 8192;

CREATE TABLE `transactions` $on_cluster
(
    `hash` String CODEC(ZSTD(1)),
    `nonce` UInt64,
    `block_hash` String CODEC(ZSTD(1)),
    `block_number` UInt64,
    `transaction_index` UInt32,
    `from_address` String CODEC(ZSTD(1)),
    `to_address` Nullable(String) CODEC(ZSTD(1)),
    `value` UInt256,
    `gas` UInt64,
    `gas_price` Nullable(UInt256),
    `input` String CODEC(ZSTD(1)),
    `block_timestamp` UInt32,
    `max_fee_per_gas` Nullable(Int64),
    `max_priority_fee_per_gas` Nullable(Int64),
    `transaction_type` Nullable(UInt32),
    `receipt_cumulative_gas_used` Nullable(UInt64),
    `receipt_gas_used` Nullable(UInt64),
    `receipt_contract_address` Nullable(String) CODEC(ZSTD(1)),
    `receipt_root` Nullable(String) CODEC(ZSTD(1)),
    `receipt_status` Nullable(UInt32),
    `receipt_effective_gas_price` Nullable(UInt256),
    `receipt_logs_count` Nullable(UInt32),
    `is_reorged` Bool DEFAULT 0,
    INDEX blocks_timestamp block_timestamp TYPE minmax GRANULARITY 1
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (block_number, hash, block_hash)
SETTINGS index_granularity = 8192;

CREATE TABLE `logs` $on_cluster
(
    `log_index` UInt32,
    `transaction_hash` String CODEC(ZSTD(1)),
    `transaction_index` UInt32,
    `block_hash` String CODEC(ZSTD(1)),
    `block_number` UInt64,
    `address` String CODEC(ZSTD(1)),
    `data` String CODEC(ZSTD(1)),
    `topics` Array(String) CODEC(ZSTD(1)),
    `is_reorged` Bool DEFAULT 0
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (block_number, transaction_hash, log_index, block_hash)
SETTINGS index_granularity = 8192;

CREATE TABLE `chain_counts` $on_cluster
(
    `active_addresses` AggregateFunction(uniq, Nullable(String)),
    `uniq_contracts` AggregateFunction(uniq, Nullable(String))
)
ENGINE = AggregatingMergeTree
ORDER BY tuple()
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW `count_active_addresses_mv` $on_cluster TO `chain_counts`
(
    `active_addresses` AggregateFunction(uniq, Nullable(String)),
    `uniq_contracts` AggregateFunction(uniq, Nullable(String))
) AS
SELECT uniqState(toNullable(from_address)) AS active_addresses
FROM `transactions`;

CREATE MATERIALIZED VIEW `count_uniq_contracts_mv` $on_cluster TO `chain_counts`
(
    `active_addresses` AggregateFunction(uniq, Nullable(String)),
    `uniq_contracts` AggregateFunction(uniq, Nullable(String))
) AS
SELECT uniqState(toNullable(address)) AS uniq_contracts
FROM `logs`;

CREATE TABLE `internal_transfers` $on_cluster
(
    `transaction_hash` String CODEC(ZSTD(1)),
    `block_timestamp` DateTime CODEC(DoubleDelta),
    `block_number` UInt64 CODEC(Delta(8), LZ4),
    `from_address` Nullable(String) CODEC(ZSTD(1)),
    `to_address` Nullable(String) CODEC(ZSTD(1)),
    `value` UInt256 CODEC(ZSTD(1)),
    `gas_limit` UInt64 CODEC(ZSTD(1)),
    `id` String CODEC(ZSTD(1)),
    `block_hash` String CODEC(ZSTD(1)),
    `is_reorged` Bool DEFAULT 0,
    INDEX block_timestamp block_timestamp TYPE minmax GRANULARITY 1
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (block_number, transaction_hash, id, block_hash)
SETTINGS index_granularity = 8192;

CREATE TABLE `native_balances` $on_cluster
(
    `address` String CODEC(ZSTD(1)),
    `block_number` UInt64 CODEC(DoubleDelta),
    `block_hash` String CODEC(ZSTD(1)),
    `block_timestamp` UInt32 CODEC(DoubleDelta),
    `value` UInt256 CODEC(ZSTD(1)),
    `is_reorged` Bool DEFAULT 0,
    INDEX block_timestamp block_timestamp TYPE minmax GRANULARITY 1
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (block_number, address, block_hash)
SETTINGS allow_nullable_key = 1, index_granularity = 8192;

CREATE TABLE `token_balances` $on_cluster
(
    `token_address` String CODEC(ZSTD(1)),
    `token_standard` LowCardinality(String) DEFAULT '',
    `holder_address` String CODEC(ZSTD(1)),
    `block_number` UInt64 CODEC(DoubleDelta),
    `block_timestamp` UInt32 CODEC(DoubleDelta),
    `value` UInt256 CODEC(ZSTD(1)),
    `token_id` UInt256 CODEC(ZSTD(1)),
    `block_hash` String CODEC(ZSTD(1)),
    `is_reorged` Bool DEFAULT 0,
    INDEX blocks_timestamp block_timestamp TYPE minmax GRANULARITY 1
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (block_number, token_address, holder_address, token_id, block_hash)
SETTINGS allow_nullable_key = 1, index_granularity = 8192;

CREATE TABLE `token_transfers` $on_cluster
(
    `token_address` String CODEC(ZSTD(1)),
    `token_standard` LowCardinality(String) DEFAULT '',
    `from_address` String CODEC(ZSTD(1)),
    `to_address` String CODEC(ZSTD(1)),
    `value` UInt256,
    `transaction_hash` String CODEC(ZSTD(1)),
    `log_index` UInt32,
    `block_timestamp` UInt32,
    `block_number` UInt64,
    `block_hash` String CODEC(ZSTD(1)),
    `operator_address` Nullable(String) CODEC(ZSTD(1)),
    `token_id` Nullable(UInt256),
    `is_nft` Bool MATERIALIZED token_id IS NOT NULL,
    `is_reorged` Bool DEFAULT 0,
    INDEX blocks_timestamp block_timestamp TYPE minmax GRANULARITY 1
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (block_number, transaction_hash, log_index, token_id, block_hash)
SETTINGS allow_nullable_key = 1, index_granularity = 8192;

"""


def upgrade() -> None:
    clickhouse_replicated = (
        os.getenv('CLICKHOUSE_REPLICATED', '').lower() in ('true', '1')
        or op.get_bind().execute("SELECT count() FROM system.replicas").scalar_one() > 0
    )

    if clickhouse_replicated:
        sql = string.Template(SCHEMA_TEMPLATE).substitute(
            on_cluster="ON CLUSTER 'stage_testnets'",
            replicated="Replicated",
            replication_path = "('/clickhouse/tables/{database}/{shard}/{table}', '{replica}-{cluster}')"
        )
    else:
        sql = string.Template(SCHEMA_TEMPLATE).substitute(
            on_cluster="",
            replicated="",
            replication_path=""
        )

    statements = filter(None, map(str.strip, sql.split(";\n")))
    for statement in statements:
        print(statement)
        # op.execute(statement)


def downgrade() -> None:
    raise NotImplementedError("Downgrade from the initial schema is not supported")
