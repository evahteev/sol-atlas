"""
create dex_trades filter optimisation.

Revision ID: e53d5b572cab
Revises: 0b5f4dd31797
Create Date: 2024-01-31 18:20:42.119057
"""
import os
import string
from functools import cache

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'e53d5b572cab'
down_revision = '0b5f4dd31797'
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
        create table `dex_trades_token_wallet_pool_factory_hash` $on_cluster
        (
            filter_column    String CODEC(ZSTD(1)),
            block_number     UInt64,
            block_hash       String CODEC(ZSTD(1)),
            block_timestamp  UInt64,
            transaction_hash String CODEC(ZSTD(1)),
            log_index        UInt64,
            transaction_type String CODEC(ZSTD(1)),
            token_addresses  Array(String),
            amounts          Array(Float64),
            amount_stable    Float64,
            amount_native    Float64,
            prices_stable    Array(Float64),
            prices_native    Array(Float64),
            pool_address     String CODEC(ZSTD(1)),
            factory_address LowCardinality(String) default '',
            lp_token_address String                default '',
            reserves         Array(Float64)        default [],
            reserves_stable  Array(Float64)        default [],
            reserves_native  Array(Float64)        default [],
            wallet_addresses   Array(String),
            is_reorged       Bool                  default 0
        )
            engine = ${replicated}ReplacingMergeTree${replication_path} ORDER BY (filter_column, block_timestamp, transaction_hash, log_index, block_hash)
                SETTINGS index_granularity = 8192;
        
        CREATE MATERIALIZED VIEW dex_trades_token_mv 
        TO dex_trades_token_wallet_pool_factory_hash
        AS
        SELECT
            arrayJoin(token_addresses) as filter_column,
            block_number as block_number,
            block_hash as block_hash,
            block_timestamp as block_timestamp,
            transaction_hash as transaction_hash,
            log_index as log_index,
            transaction_type as transaction_type,
            token_addresses as token_addresses,
            amounts as amounts,
            amount_stable as amount_stable,
            amount_native as amount_native,
            prices_stable as prices_stable,
            prices_native as prices_native,
            pool_address as pool_address,
            factory_address as factory_address,
            lp_token_address as lp_token_address,
            reserves as reserves,
            reserves_stable as reserves_stable,
            reserves_native as reserves_native,
            [wallet_address] as wallet_addresses,
            is_reorged as is_reorged
        FROM dex_trades;
        
        CREATE MATERIALIZED VIEW dex_trades_wallet_mv 
        TO dex_trades_token_wallet_pool_factory_hash
        AS
        SELECT
            wallet_address as filter_column,
            block_number as block_number,
            block_hash as block_hash,
            block_timestamp as block_timestamp,
            transaction_hash as transaction_hash,
            log_index as log_index,
            transaction_type as transaction_type,
            token_addresses as token_addresses,
            amounts as amounts,
            amount_stable as amount_stable,
            amount_native as amount_native,
            prices_stable as prices_stable,
            prices_native as prices_native,
            pool_address as pool_address,
            factory_address as factory_address,
            lp_token_address as lp_token_address,
            reserves as reserves,
            reserves_stable as reserves_stable,
            reserves_native as reserves_native,
            [wallet_address] as wallet_addresses,
            is_reorged as is_reorged
        FROM dex_trades;
        
        CREATE MATERIALIZED VIEW dex_trades_pool_mv 
        TO dex_trades_token_wallet_pool_factory_hash
        AS
        SELECT
            pool_address as filter_column,
            block_number as block_number,
            block_hash as block_hash,
            block_timestamp as block_timestamp,
            transaction_hash as transaction_hash,
            log_index as log_index,
            transaction_type as transaction_type,
            token_addresses as token_addresses,
            amounts as amounts,
            amount_stable as amount_stable,
            amount_native as amount_native,
            prices_stable as prices_stable,
            prices_native as prices_native,
            pool_address as pool_address,
            factory_address as factory_address,
            lp_token_address as lp_token_address,
            reserves as reserves,
            reserves_stable as reserves_stable,
            reserves_native as reserves_native,
            [wallet_address] as wallet_addresses,
            is_reorged as is_reorged
        FROM dex_trades;
        
        CREATE MATERIALIZED VIEW dex_trades_factory_mv 
        TO dex_trades_token_wallet_pool_factory_hash
        AS
        SELECT
            factory_address as filter_column,
            block_number as block_number,
            block_hash as block_hash,
            block_timestamp as block_timestamp,
            transaction_hash as transaction_hash,
            log_index as log_index,
            transaction_type as transaction_type,
            token_addresses as token_addresses,
            amounts as amounts,
            amount_stable as amount_stable,
            amount_native as amount_native,
            prices_stable as prices_stable,
            prices_native as prices_native,
            pool_address as pool_address,
            factory_address as factory_address,
            lp_token_address as lp_token_address,
            reserves as reserves,
            reserves_stable as reserves_stable,
            reserves_native as reserves_native,
            [wallet_address] as wallet_addresses,
            is_reorged as is_reorged
        FROM dex_trades;
        
        CREATE MATERIALIZED VIEW dex_trades_transaction_hash_mv 
        TO dex_trades_token_wallet_pool_factory_hash
        AS
        SELECT
            transaction_hash as filter_column,
            block_number as block_number,
            block_hash as block_hash,
            block_timestamp as block_timestamp,
            transaction_hash as transaction_hash,
            log_index as log_index,
            transaction_type as transaction_type,
            token_addresses as token_addresses,
            amounts as amounts,
            amount_stable as amount_stable,
            amount_native as amount_native,
            prices_stable as prices_stable,
            prices_native as prices_native,
            pool_address as pool_address,
            factory_address as factory_address,
            lp_token_address as lp_token_address,
            reserves as reserves,
            reserves_stable as reserves_stable,
            reserves_native as reserves_native,
            [wallet_address] as wallet_addresses,
            is_reorged as is_reorged
        FROM dex_trades;    
    """

    on_cluster = os.getenv('ON_CLUSTER', '').lower() in ('true', '1')
    if on_cluster:
        on_cluster = "ON CLUSTER '{cluster}'"
    else:
        on_cluster = ""

    if is_clickhouse_replicated():
        sql = string.Template(schema_template).substitute(
            on_cluster=on_cluster,
            replicated="Replicated",
            replication_path="('/clickhouse/tables/{database}/{shard}/{table}', '{replica}-{cluster}')",
        )
    else:
        sql = string.Template(schema_template).substitute(
            on_cluster="",
            replicated="",
            replication_path=""
        )

    statements = filter(None, map(str.strip, sql.split(";")))
    for statement in statements:
        op.execute(statement)


def downgrade() -> None:
    schema_template = """DROP VIEW dex_trades_token_mv $on_cluster SYNC;
                         DROP VIEW dex_trades_wallet_mv $on_cluster SYNC;
                         DROP VIEW dex_trades_factory_mv $on_cluster SYNC;
                         DROP VIEW dex_trades_pool_mv $on_cluster SYNC;
                         DROP VIEW dex_trades_transaction_hash_mv $on_cluster SYNC;
                         DROP TABLE dex_trades_token_wallet_pool_factory_hash $on_cluster SYNC;"""

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

    statements = filter(None, map(str.strip, sql.split(";")))
    for statement in statements:
        op.execute(statement)
