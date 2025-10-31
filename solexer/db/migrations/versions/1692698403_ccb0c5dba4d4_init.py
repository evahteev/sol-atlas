"""
Init.

Revision ID: ccb0c5dba4d4
Revises:
Create Date: 2023-07-31 17:30:50.941585
"""

import os
import string

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'ccb0c5dba4d4'
down_revision = None
branch_labels = None
depends_on = None

SCHEMA_TEMPLATE = """
CREATE TABLE `blocks` $on_cluster
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

CREATE TABLE `chain_counts` $on_cluster
(
    `active_addresses` AggregateFunction(uniq, Nullable(String)),
    `uniq_contracts` AggregateFunction(uniq, Nullable(String))
)
ENGINE = AggregatingMergeTree
ORDER BY tuple()
SETTINGS index_granularity = 8192;

CREATE TABLE `contracts`
(
    `address` String CODEC(ZSTD(1)),
    `bytecode` String CODEC(ZSTD(1)),
    `function_sighashes` Array(String) CODEC(ZSTD(1)),
    `is_erc20` UInt8,
    `is_erc721` UInt8,
    `block_number` UInt64
)
ENGINE = EmbeddedRocksDB
PRIMARY KEY address;

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

CREATE MATERIALIZED VIEW `count_active_addresses_mv` $on_cluster TO `chain_counts`
(
    `active_addresses` AggregateFunction(uniq, Nullable(String)),
    `uniq_contracts` AggregateFunction(uniq, Nullable(String))
) AS
SELECT uniqState(toNullable(from_address)) AS active_addresses
FROM `transactions`;

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

CREATE MATERIALIZED VIEW `count_uniq_contracts_mv` $on_cluster TO `chain_counts`
(
    `active_addresses` AggregateFunction(uniq, Nullable(String)),
    `uniq_contracts` AggregateFunction(uniq, Nullable(String))
) AS
SELECT uniqState(toNullable(address)) AS uniq_contracts
FROM `logs`;

CREATE TABLE `errors` $on_cluster
(
    `item_id` String CODEC(ZSTD(1)),
    `timestamp` UInt32 CODEC(Delta(4), LZ4),
    `block_number` UInt64 CODEC(Delta(8), LZ4),
    `block_timestamp` UInt32 CODEC(Delta(4), LZ4),
    `kind` LowCardinality(String),
    `data_json` String CODEC(ZSTD(1)),
    `block_hash` String CODEC(ZSTD(1))
)
ENGINE = ${replicated}MergeTree${replication_path}
PARTITION BY toYYYYMM(fromUnixTimestamp(timestamp))
ORDER BY timestamp
SETTINGS index_granularity = 8192;

CREATE TABLE `events` $on_cluster
(
    `log_index` UInt32,
    `transaction_hash` String CODEC(ZSTD(1)),
    `transaction_index` UInt32,
    `block_hash` String CODEC(ZSTD(1)),
    `block_number` UInt64,
    `contract_address` String CODEC(ZSTD(1)),
    `data` String CODEC(ZSTD(1)),
    `topics` Array(String) CODEC(ZSTD(1)),
    `event_name` String CODEC(ZSTD(1)),
    `event_signature_hash` String ALIAS topics[1],
    `topic_count` UInt8 ALIAS toUInt8(length(topics))
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
PARTITION BY intDivOrZero(block_number, 100000)
ORDER BY (contract_address, topics[1], transaction_hash, log_index)
SETTINGS index_granularity = 8192;

CREATE TABLE `geth_traces` $on_cluster
(
    `transaction_hash` String CODEC(ZSTD(1)),
    `block_timestamp` DateTime CODEC(DoubleDelta),
    `block_number` UInt64 CODEC(Delta(8), LZ4),
    `traces_json` String CODEC(ZSTD(1)),
    `block_hash` String CODEC(ZSTD(1)),
    `is_reorged` Bool DEFAULT 0,
    INDEX blocks_timestamp block_timestamp TYPE minmax GRANULARITY 1
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (block_number, transaction_hash, block_hash)
SETTINGS index_granularity = 8192;

CREATE TABLE `geth_traces_transaction_hash` $on_cluster
(
    `transaction_hash` String CODEC(ZSTD(1)),
    `block_timestamp` DateTime CODEC(DoubleDelta),
    `block_number` UInt64 CODEC(Delta(8), LZ4),
    `traces_json` String CODEC(ZSTD(1)),
    `block_hash` String CODEC(ZSTD(1)),
    `is_reorged` Bool DEFAULT 0
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (transaction_hash, block_hash)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW `geth_traces_by_transaction_hash` $on_cluster TO `geth_traces_transaction_hash`
(
    `transaction_hash` String,
    `block_timestamp` DateTime,
    `block_number` UInt64,
    `traces_json` String,
    `block_hash` String,
    `is_reorged` Bool
) AS
SELECT
    transaction_hash,
    block_timestamp,
    block_number,
    traces_json,
    block_hash,
    is_reorged
FROM `geth_traces`;

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

CREATE TABLE `internal_transfers_address` $on_cluster
(
    `address` String CODEC(ZSTD(1)),
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
    INDEX block_number block_number TYPE minmax GRANULARITY 1
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (address, from_address, to_address, transaction_hash, id, block_hash)
SETTINGS allow_nullable_key = 1, index_granularity = 8192;

CREATE MATERIALIZED VIEW `internal_transfers_from_address_mv` $on_cluster TO `internal_transfers_address`
(
    `address` Nullable(String),
    `transaction_hash` String,
    `block_timestamp` DateTime,
    `block_number` UInt64,
    `from_address` Nullable(String),
    `to_address` Nullable(String),
    `value` UInt256,
    `gas_limit` UInt64,
    `id` String,
    `block_hash` String,
    `is_reorged` Bool
) AS
SELECT
    from_address AS address,
    transaction_hash,
    block_timestamp,
    block_number,
    from_address,
    to_address,
    value,
    gas_limit,
    id,
    block_hash,
    is_reorged
FROM `internal_transfers`
WHERE from_address IS NOT NULL;

CREATE MATERIALIZED VIEW `internal_transfers_to_address_mv` $on_cluster TO `internal_transfers_address`
(
    `address` Nullable(String),
    `transaction_hash` String,
    `block_timestamp` DateTime,
    `block_number` UInt64,
    `from_address` Nullable(String),
    `to_address` Nullable(String),
    `value` UInt256,
    `gas_limit` UInt64,
    `id` String,
    `block_hash` String,
    `is_reorged` Bool
) AS
SELECT
    to_address AS address,
    transaction_hash,
    block_timestamp,
    block_number,
    from_address,
    to_address,
    value,
    gas_limit,
    id,
    block_hash,
    is_reorged
FROM `internal_transfers`
WHERE to_address IS NOT NULL;

CREATE TABLE `internal_transfers_transaction_hash` $on_cluster
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
    `is_reorged` Bool DEFAULT 0
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (transaction_hash, block_number, id, block_hash)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW `internal_transfers_transaction_hash_mv` $on_cluster TO `internal_transfers_transaction_hash`
(
    `transaction_hash` String,
    `block_timestamp` DateTime,
    `block_number` UInt64,
    `from_address` Nullable(String),
    `to_address` Nullable(String),
    `value` UInt256,
    `gas_limit` UInt64,
    `id` String,
    `block_hash` String,
    `is_reorged` Bool
) AS
SELECT
    transaction_hash,
    block_timestamp,
    block_number,
    from_address,
    to_address,
    value,
    gas_limit,
    id,
    block_hash,
    is_reorged
FROM `internal_transfers`;

CREATE TABLE `logs_address` $on_cluster
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
ORDER BY (address, transaction_hash, log_index, block_hash)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW `logs_by_address_mv` $on_cluster TO `logs_address`
(
    `log_index` UInt32,
    `transaction_hash` String,
    `transaction_index` UInt32,
    `block_hash` String,
    `block_number` UInt64,
    `address` String,
    `data` String,
    `topics` Array(String),
    `is_reorged` Bool
) AS
SELECT
    log_index,
    transaction_hash,
    transaction_index,
    block_hash,
    block_number,
    address,
    data,
    topics,
    is_reorged
FROM `logs`;


CREATE TABLE `logs_transaction_hash` $on_cluster
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
ORDER BY (transaction_hash, log_index, block_hash)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW `logs_by_transaction_hash_mv` $on_cluster TO `logs_transaction_hash`
(
    `log_index` UInt32,
    `transaction_hash` String,
    `transaction_index` UInt32,
    `block_hash` String,
    `block_number` UInt64,
    `address` String,
    `data` String,
    `topics` Array(String),
    `is_reorged` Bool
) AS
SELECT
    log_index,
    transaction_hash,
    transaction_index,
    block_hash,
    block_number,
    address,
    data,
    topics,
    is_reorged
FROM `logs`;

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

CREATE TABLE `token_transfers_address` $on_cluster
(
    `address` String CODEC(ZSTD(1)),
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
    `is_reorged` Bool DEFAULT 0
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (address, token_standard, token_id, transaction_hash, log_index, block_hash)
SETTINGS allow_nullable_key = 1, index_granularity = 8192;

CREATE MATERIALIZED VIEW `token_transfers_from_address_mv` $on_cluster TO `token_transfers_address`
(
    `address` String,
    `token_address` String,
    `token_standard` LowCardinality(String),
    `from_address` String,
    `to_address` String,
    `value` UInt256,
    `transaction_hash` String,
    `log_index` UInt32,
    `block_timestamp` UInt32,
    `block_number` UInt64,
    `block_hash` String,
    `operator_address` Nullable(String),
    `token_id` Nullable(UInt256),
    `is_reorged` Bool
) AS
SELECT
    from_address AS address,
    token_address,
    token_standard,
    from_address,
    to_address,
    value,
    transaction_hash,
    log_index,
    block_timestamp,
    block_number,
    block_hash,
    operator_address,
    token_id,
    is_reorged
FROM `token_transfers`;

CREATE MATERIALIZED VIEW `token_transfers_to_address_mv` $on_cluster TO `token_transfers_address`
(
    `address` String,
    `token_address` String,
    `token_standard` LowCardinality(String),
    `from_address` String,
    `to_address` String,
    `value` UInt256,
    `transaction_hash` String,
    `log_index` UInt32,
    `block_timestamp` UInt32,
    `block_number` UInt64,
    `block_hash` String,
    `operator_address` Nullable(String),
    `token_id` Nullable(UInt256),
    `is_reorged` Bool
) AS
SELECT
    to_address AS address,
    token_address,
    token_standard,
    from_address,
    to_address,
    value,
    transaction_hash,
    log_index,
    block_timestamp,
    block_number,
    block_hash,
    operator_address,
    token_id,
    is_reorged
FROM `token_transfers`;

CREATE MATERIALIZED VIEW `token_transfers_token_address_mv` $on_cluster TO `token_transfers_address`
(
    `address` String,
    `token_address` String,
    `token_standard` LowCardinality(String),
    `from_address` String,
    `to_address` String,
    `value` UInt256,
    `transaction_hash` String,
    `log_index` UInt32,
    `block_timestamp` UInt32,
    `block_number` UInt64,
    `block_hash` String,
    `operator_address` Nullable(String),
    `token_id` Nullable(UInt256),
    `is_reorged` Bool
) AS
SELECT
    token_address AS address,
    token_address,
    token_standard,
    from_address,
    to_address,
    value,
    transaction_hash,
    log_index,
    block_timestamp,
    block_number,
    block_hash,
    operator_address,
    token_id,
    is_reorged
FROM `token_transfers`;

CREATE TABLE `token_transfers_transaction_hash` $on_cluster
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
    `is_reorged` Bool DEFAULT 0
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (transaction_hash, log_index, token_id, block_hash)
SETTINGS allow_nullable_key = 1, index_granularity = 8192;

CREATE MATERIALIZED VIEW `token_transfers_transaction_hash_mv` $on_cluster TO `token_transfers_transaction_hash`
(
    `token_address` String,
    `token_standard` LowCardinality(String),
    `from_address` String,
    `to_address` String,
    `value` UInt256,
    `transaction_hash` String,
    `log_index` UInt32,
    `block_timestamp` UInt32,
    `block_number` UInt64,
    `block_hash` String,
    `operator_address` Nullable(String),
    `token_id` Nullable(UInt256),
    `is_reorged` Bool
) AS
SELECT
    token_address,
    token_standard,
    from_address,
    to_address,
    value,
    transaction_hash,
    log_index,
    block_timestamp,
    block_number,
    block_hash,
    operator_address,
    token_id,
    is_reorged
FROM `token_transfers`;

CREATE TABLE `tokens`
(
    `address` String CODEC(ZSTD(1)),
    `name` String CODEC(ZSTD(1)),
    `symbol` String CODEC(ZSTD(1)),
    `decimals` UInt8,
    `total_supply` UInt256
)
ENGINE = EmbeddedRocksDB
PRIMARY KEY address;

CREATE TABLE `traces` $on_cluster
(
    `transaction_hash` Nullable(String) CODEC(ZSTD(1)),
    `transaction_index` Nullable(UInt32),
    `from_address` Nullable(String) CODEC(ZSTD(1)),
    `to_address` String CODEC(ZSTD(1)),
    `value` UInt256,
    `input` Nullable(String) CODEC(ZSTD(1)),
    `output` Nullable(String) CODEC(ZSTD(1)),
    `trace_type` String CODEC(ZSTD(1)),
    `call_type` Nullable(String) CODEC(ZSTD(1)),
    `reward_type` Nullable(String) CODEC(ZSTD(1)),
    `gas` Nullable(UInt64),
    `gas_used` Nullable(UInt64),
    `subtraces` UInt32,
    `trace_address` Array(UInt64) CODEC(ZSTD(1)),
    `error` Nullable(String) CODEC(ZSTD(1)),
    `status` UInt32,
    `block_timestamp` UInt32,
    `block_number` UInt64,
    `block_hash` String CODEC(ZSTD(1)),
    `trace_id` String CODEC(ZSTD(1)),
    `is_reorged` Bool DEFAULT 0
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
PARTITION BY toYYYYMMDD(FROM_UNIXTIME(block_timestamp))
ORDER BY trace_id
SETTINGS index_granularity = 8192;

CREATE TABLE `transactions_address` $on_cluster
(
    `address` String CODEC(ZSTD(1)),
    `hash` String CODEC(ZSTD(1)),
    `nonce` UInt64,
    `block_hash` String CODEC(ZSTD(1)),
    `block_number` UInt64,
    `transaction_index` UInt32,
    `from_address` String CODEC(ZSTD(1)),
    `to_address` Nullable(String) CODEC(ZSTD(1)),
    `value` UInt256,
    `gas` UInt64,
    `gas_price` Nullable(UInt64),
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
    `is_reorged` Bool DEFAULT 0
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (address, from_address, to_address, hash, block_hash)
SETTINGS allow_nullable_key = 1, index_granularity = 8192;

CREATE MATERIALIZED VIEW `transactions_by_from_address_mv` $on_cluster TO `transactions_address`
(
    `address` String,
    `hash` String,
    `nonce` UInt64,
    `block_hash` String,
    `block_number` UInt64,
    `transaction_index` UInt32,
    `from_address` String,
    `to_address` Nullable(String),
    `value` UInt256,
    `gas` UInt64,
    `gas_price` Nullable(UInt256),
    `input` String,
    `block_timestamp` UInt32,
    `max_fee_per_gas` Nullable(Int64),
    `max_priority_fee_per_gas` Nullable(Int64),
    `transaction_type` Nullable(UInt32),
    `receipt_cumulative_gas_used` Nullable(UInt64),
    `receipt_gas_used` Nullable(UInt64),
    `receipt_contract_address` Nullable(String),
    `receipt_root` Nullable(String),
    `receipt_status` Nullable(UInt32),
    `receipt_effective_gas_price` Nullable(UInt256),
    `receipt_logs_count` Nullable(UInt32),
    `is_reorged` Bool
) AS
SELECT
    from_address AS address,
    hash,
    nonce,
    block_hash,
    block_number,
    transaction_index,
    from_address,
    to_address,
    value,
    gas,
    gas_price,
    input,
    block_timestamp,
    max_fee_per_gas,
    max_priority_fee_per_gas,
    transaction_type,
    receipt_cumulative_gas_used,
    receipt_gas_used,
    receipt_contract_address,
    receipt_root,
    receipt_status,
    receipt_effective_gas_price,
    receipt_logs_count,
    is_reorged
FROM `transactions`
WHERE from_address IS NOT NULL;

CREATE TABLE `transactions_hash` $on_cluster
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
    `gas_price` Nullable(UInt64),
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
    `is_reorged` Bool DEFAULT 0
)
ENGINE = ${replicated}ReplacingMergeTree${replication_path}
ORDER BY (hash, block_number, block_hash)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW `transactions_by_hash_mv` $on_cluster TO `transactions_hash`
(
    `hash` String,
    `nonce` UInt64,
    `block_hash` String,
    `block_number` UInt64,
    `transaction_index` UInt32,
    `from_address` String,
    `to_address` Nullable(String),
    `value` UInt256,
    `gas` UInt64,
    `gas_price` Nullable(UInt256),
    `input` String,
    `block_timestamp` UInt32,
    `max_fee_per_gas` Nullable(Int64),
    `max_priority_fee_per_gas` Nullable(Int64),
    `transaction_type` Nullable(UInt32),
    `receipt_cumulative_gas_used` Nullable(UInt64),
    `receipt_gas_used` Nullable(UInt64),
    `receipt_contract_address` Nullable(String),
    `receipt_root` Nullable(String),
    `receipt_status` Nullable(UInt32),
    `receipt_effective_gas_price` Nullable(UInt256),
    `receipt_logs_count` Nullable(UInt32),
    `is_reorged` Bool
) AS
SELECT
    hash,
    nonce,
    block_hash,
    block_number,
    transaction_index,
    from_address,
    to_address,
    value,
    gas,
    gas_price,
    input,
    block_timestamp,
    max_fee_per_gas,
    max_priority_fee_per_gas,
    transaction_type,
    receipt_cumulative_gas_used,
    receipt_gas_used,
    receipt_contract_address,
    receipt_root,
    receipt_status,
    receipt_effective_gas_price,
    receipt_logs_count,
    is_reorged
FROM `transactions`;

CREATE MATERIALIZED VIEW `transactions_by_to_address_mv` $on_cluster TO `transactions_address`
(
    `address` Nullable(String),
    `hash` String,
    `nonce` UInt64,
    `block_hash` String,
    `block_number` UInt64,
    `transaction_index` UInt32,
    `from_address` String,
    `to_address` Nullable(String),
    `value` UInt256,
    `gas` UInt64,
    `gas_price` Nullable(UInt256),
    `input` String,
    `block_timestamp` UInt32,
    `max_fee_per_gas` Nullable(Int64),
    `max_priority_fee_per_gas` Nullable(Int64),
    `transaction_type` Nullable(UInt32),
    `receipt_cumulative_gas_used` Nullable(UInt64),
    `receipt_gas_used` Nullable(UInt64),
    `receipt_contract_address` Nullable(String),
    `receipt_root` Nullable(String),
    `receipt_status` Nullable(UInt32),
    `receipt_effective_gas_price` Nullable(UInt256),
    `receipt_logs_count` Nullable(UInt32),
    `is_reorged` Bool
) AS
SELECT
    to_address AS address,
    hash,
    nonce,
    block_hash,
    block_number,
    transaction_index,
    from_address,
    to_address,
    value,
    gas,
    gas_price,
    input,
    block_timestamp,
    max_fee_per_gas,
    max_priority_fee_per_gas,
    transaction_type,
    receipt_cumulative_gas_used,
    receipt_gas_used,
    receipt_contract_address,
    receipt_root,
    receipt_status,
    receipt_effective_gas_price,
    receipt_logs_count,
    is_reorged
FROM `transactions`
WHERE to_address IS NOT NULL;

CREATE TABLE etl_delay $on_cluster
(
    `entity_type` String CODEC(ZSTD(1)),
    `block_number` UInt64 CODEC(Delta(8), LZ4),
    `timestamp` UInt32,
    `indexed_at` DateTime,
    `delay` Int32,
    `chain_id` Int32
)
ENGINE = ${replicated}MergeTree${replication_path}
ORDER BY block_number
TTL indexed_at + toIntervalDay(3)
SETTINGS index_granularity = 8192;

CREATE MATERIALIZED VIEW etl_delay_blocks_mv $on_cluster TO etl_delay
(
    `block_number` UInt64,
    `timestamp` UInt32,
    `indexed_at` DateTime,
    `delay` Int32,
    `chain_id` UInt8,
    `entity_type` String
) AS
SELECT
    number AS block_number,
    timestamp,
    now() AS indexed_at,
    now() - toDateTime(timestamp) AS delay,
    1 AS chain_id,
    'block' AS entity_type
FROM `blocks`;

CREATE MATERIALIZED VIEW etl_delay_geth_traces_mv $on_cluster TO etl_delay
(
    `block_number` UInt64,
    `timestamp` DateTime,
    `indexed_at` DateTime,
    `delay` Int32,
    `chain_id` UInt8,
    `entity_type` String
) AS
SELECT
    block_number,
    block_timestamp AS timestamp,
    now() AS indexed_at,
    now() - toDateTime(timestamp) AS delay,
    1 AS chain_id,
    'geth_trace' AS entity_type
FROM `geth_traces`;

CREATE MATERIALIZED VIEW etl_delay_internal_transfers_mv $on_cluster TO etl_delay
(
    `block_number` UInt64,
    `timestamp` DateTime,
    `indexed_at` DateTime,
    `delay` Int32,
    `chain_id` UInt8,
    `entity_type` String
) AS
SELECT
    block_number,
    block_timestamp AS timestamp,
    now() AS indexed_at,
    now() - toDateTime(timestamp) AS delay,
    1 AS chain_id,
    'internal_transfer' AS entity_type
FROM `internal_transfers`;

CREATE MATERIALIZED VIEW etl_delay_transactions_mv $on_cluster TO etl_delay
(
    `block_number` UInt64,
    `timestamp` UInt32,
    `indexed_at` DateTime,
    `delay` Int32,
    `chain_id` UInt8,
    `entity_type` String
) AS
SELECT
    block_number,
    block_timestamp AS timestamp,
    now() AS indexed_at,
    now() - toDateTime(timestamp) AS delay,
    1 AS chain_id,
    'transaction' AS entity_type
FROM `transactions`;
"""


def upgrade() -> None:
    clickhouse_replicated = (
        os.getenv('CLICKHOUSE_REPLICATED', '').lower() in ('true', '1')
        or op.get_bind().execute(text("SELECT count() FROM system.replicas")).scalar_one() > 0
    )

    on_cluster = os.getenv('ON_CLUSTER', '').lower() in ('true', '1')
    if on_cluster:
        on_cluster = "ON CLUSTER '{cluster}'"
    else:
        on_cluster = ""
    if clickhouse_replicated:
        sql = string.Template(SCHEMA_TEMPLATE).substitute(
            on_cluster=on_cluster,
            replicated="Replicated",
            replication_path="('/clickhouse/tables/{database}/{shard}/{table}', '{replica}-{cluster}')",
        )
    else:
        sql = string.Template(SCHEMA_TEMPLATE).substitute(
            on_cluster=on_cluster, replicated="", replication_path=""
        )

    statements = filter(None, map(str.strip, sql.split(";\n")))
    for statement in statements:
        op.execute(statement)


def downgrade() -> None:
    raise NotImplementedError("Downgrade from the initial schema is not supported")
