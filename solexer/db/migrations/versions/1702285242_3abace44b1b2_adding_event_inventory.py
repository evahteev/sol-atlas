"""
adding event_inventory.

Revision ID: 3abace44b1b2
Revises: ccb0c5dba4d4
Create Date: 2023-12-11 10:00:42.927527
"""
import os
import string
from functools import cache

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '3abace44b1b2'
down_revision = 'ccb0c5dba4d4'
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
        
        CREATE TABLE IF NOT EXISTS `event_inventory` $on_cluster
        (
            `event_signature_hash_and_log_topic_count` Tuple(LowCardinality(String), UInt8),
            `event_signature_hash` String ALIAS event_signature_hash_and_log_topic_count.1,
            `event_topic_count` UInt8 ALIAS event_signature_hash_and_log_topic_count.2,
            `namespace` Array(LowCardinality(String)),
            `contract_name` Array(LowCardinality(String)),
            `event_signature` LowCardinality(String),
            `event_name` LowCardinality(String),
            `event_abi_json` String CODEC(ZSTD(1))
        )
        ENGINE = ${replicated}ReplacingMergeTree${replication_path}
        PRIMARY KEY event_signature_hash_and_log_topic_count;
        
        CREATE TABLE IF NOT EXISTS `event_inventory_src` $on_cluster
        (
            `event_signature_hash` LowCardinality(String),
            `event_signature` LowCardinality(String),
            `event_topic_count` UInt8,
            `event_name` LowCardinality(String),
            `namespace` LowCardinality(String),
            `contract_name` LowCardinality(String),
            `event_abi_json` String CODEC(ZSTD(1))
        )
        ENGINE = ${replicated}ReplacingMergeTree${replication_path}
        ORDER BY (event_signature, event_topic_count, namespace);
        
        CREATE MATERIALIZED VIEW IF NOT EXISTS `event_inventory_mv` $on_cluster TO `event_inventory`
        (
            `event_signature_hash_and_log_topic_count` Tuple(LowCardinality(String), UInt8),
            `namespace` LowCardinality(String),
            `contract_name` LowCardinality(String),
            `event_signature` LowCardinality(String),
            `event_name` LowCardinality(String),
            `event_abi_json` String
        ) AS
        WITH src AS
            (
                SELECT
                    (event_signature_hash, event_topic_count) AS event_signature_hash_and_log_topic_count,
                    groupArray(namespace) AS namespace,
                    groupArray(contract_name) AS contract_name,
                    event_signature,
                    event_name,
                    event_abi_json
                FROM `event_inventory_src`
                GROUP BY event_signature_hash, event_topic_count, event_signature, event_name, event_abi_json
            )
        SELECT
            src.event_signature_hash_and_log_topic_count,
            arraySort(arrayDistinct(arrayConcat(dst.namespace, src.namespace))) AS namespace,
            arraySort(arrayDistinct(arrayConcat(dst.contract_name, src.contract_name))) AS contract_name,
            src.event_signature,
            src.event_name,
            src.event_abi_json
        FROM src
        LEFT JOIN `event_inventory` AS dst USING (event_signature_hash_and_log_topic_count);
    
        CREATE TABLE IF NOT EXISTS `dex_pools` $on_cluster
        (
            `address` String CODEC(ZSTD(1)),
            `factory_address` LowCardinality(String),
            `token_addresses` Array(String) CODEC(ZSTD(1)),
            `lp_token_addresses` Array(String) CODEC(ZSTD(1)),
            `fee` UInt16
        )
        ENGINE = EmbeddedRocksDB
        PRIMARY KEY address;

        """

    on_cluster = os.getenv('ON_CLUSTER', '').lower() in ('true', '1')
    if on_cluster:
        on_cluster = "ON CLUSTER '{cluster}'"
    else:
        on_cluster = ""

    if is_clickhouse_replicated():
        on_cluster = on_cluster
        replicated = "Replicated"
        replication_path = "('/clickhouse/tables/{database}/{shard}/${table}', '{replica}-{cluster}')"
    else:
        on_cluster = ""
        replicated = ""
        replication_path = ""

    sql = string.Template(schema_template).substitute(
        on_cluster=on_cluster,
        replicated=replicated,
        replication_path=replication_path
    )
    statements = filter(None, map(str.strip, sql.split(";\n")))
    for statement in statements:
        op.execute(statement)


def downgrade() -> None:
    schema_template = """
        DROP TABLE dex_pools $on_cluster SYNC;
        DROP VIEW event_inventory_mv $on_cluster SYNC;
        DROP TABLE event_inventory_src $on_cluster SYNC;
        DROP TABLE event_inventory $on_cluster SYNC;
        
        CREATE TABLE `event_inventory` $on_cluster
        (
            `event_signature_hash_and_log_topic_count` Tuple(LowCardinality(String), UInt8),
            `event_signature_hash` String ALIAS event_signature_hash_and_log_topic_count.1,
            `event_topic_count` UInt8 ALIAS event_signature_hash_and_log_topic_count.2,
            `abi_types` Array(LowCardinality(String)),
            `event_signature` LowCardinality(String),
            `event_name` LowCardinality(String),
            `event_abi_json` String CODEC(ZSTD(1))
        )
        ENGINE = EmbeddedRocksDB
        PRIMARY KEY event_signature_hash_and_log_topic_count;
        
        CREATE TABLE `event_inventory_src` $on_cluster
        (
            `event_signature_hash` LowCardinality(String),
            `event_signature` LowCardinality(String),
            `event_topic_count` UInt8,
            `event_name` LowCardinality(String),
            `abi_type` String,
            `event_abi_json` String CODEC(ZSTD(1))
        )
        ENGINE = ${replicated}ReplacingMergeTree${replication_path}
        ORDER BY (event_signature, event_topic_count, abi_type)
        SETTINGS index_granularity = 8192;
        
        CREATE MATERIALIZED VIEW `event_inventory_mv` $on_cluster TO `event_inventory`
        (
            `event_signature_hash_and_log_topic_count` Tuple(LowCardinality(String), UInt8),
            `abi_types` Array(String),
            `event_signature` LowCardinality(String),
            `event_name` LowCardinality(String),
            `event_abi_json` String
        ) AS
        WITH src AS
            (
                SELECT
                    (event_signature_hash, event_topic_count) AS event_signature_hash_and_log_topic_count,
                    groupArray(abi_type) AS abi_types,
                    event_signature,
                    event_name,
                    event_abi_json
                FROM `event_inventory_src`
                GROUP BY event_signature_hash, event_topic_count, event_signature, event_name, event_abi_json
            )
        SELECT
            src.event_signature_hash_and_log_topic_count,
            arraySort(arrayDistinct(arrayConcat(dst.abi_types, src.abi_types))) AS abi_types,
            src.event_signature,
            src.event_name,
            src.event_abi_json
        FROM src
        LEFT JOIN `event_inventory` AS dst USING (event_signature_hash_and_log_topic_count)
        SETTINGS join_algorithm = 'direct';
        
     CREATE TABLE events
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
     ENGINE = ReplacingMergeTree
     PARTITION BY intDivOrZero(block_number, 100000)
     ORDER BY (contract_address, topics[1], transaction_hash, log_index)
     SETTINGS index_granularity = 8192;
     
      CREATE MATERIALIZED VIEW logs_to_events_mv TO events\n
     (
         `log_index` UInt32,
         `transaction_hash` String,
         `transaction_index` UInt32,
         `block_hash` String,
         `block_number` UInt64,
         `data` String,
         `topics` Array(String),
         `contract_address` String,
         `event_name` LowCardinality(String)
     ) AS
     SELECT
         logs.log_index,
         logs.transaction_hash,
         logs.transaction_index,
         logs.block_hash,
         logs.block_number,
         logs.data,
         logs.topics,
         logs.address AS contract_address,
         info.event_name
     FROM logs AS logs
     INNER JOIN event_inventory AS info ON (logs.topics[1], 
        toUInt8(length(logs.topics))) = info.event_signature_hash_and_log_topic_count
     SETTINGS join_algorithm = 'direct'
    """

    on_cluster = os.getenv('ON_CLUSTER', '').lower() in ('true', '1')
    if on_cluster:
        on_cluster = "ON CLUSTER '{cluster}'"
    else:
        on_cluster = ""

    if is_clickhouse_replicated():
        on_cluster = on_cluster
        replicated = "Replicated"
        replication_path = "('/clickhouse/tables/{database}/{shard}/{table}', '{replica}-{cluster}')"
    else:
        on_cluster = ""
        replicated = ""
        replication_path = ""
    _ = replicated

    sql = string.Template(schema_template).substitute(on_cluster=on_cluster, replicated=replicated,
                                                      replication_path=replication_path)
    statements = filter(None, map(str.strip, sql.split(";\n")))
    for statement in statements:
        op.execute(statement)
