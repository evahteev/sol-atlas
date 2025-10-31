"""Update materialized views to include swap_type column

Revision ID: update_materialized_views_swap_type
Revises: add_swap_type_column
Create Date: 2025-01-05 12:03:20.000000

"""
from alembic import op
from sqlalchemy import text
import sqlalchemy as sa
import os
import string
from functools import cache


# revision identifiers, used by Alembic.
revision = '1757007000_update_materialized_views_swap_type'
down_revision = '1757006980_add_swap_type_column'
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
    ALTER TABLE dex_trades_token_wallet_pool_factory_hash $on_cluster ADD COLUMN swap_type String DEFAULT 'buy' CODEC(ZSTD(1)) AFTER transaction_type;
    
    DROP VIEW dex_trades_token_mv $on_cluster;
    DROP VIEW dex_trades_wallet_mv $on_cluster;
    DROP VIEW dex_trades_pool_mv $on_cluster;
    DROP VIEW dex_trades_factory_mv $on_cluster;
    DROP VIEW dex_trades_transaction_hash_mv $on_cluster;
    
    CREATE MATERIALIZED VIEW dex_trades_token_mv $on_cluster
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
        swap_type as swap_type,
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
    
    CREATE MATERIALIZED VIEW dex_trades_wallet_mv $on_cluster
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
        swap_type as swap_type,
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
    
    CREATE MATERIALIZED VIEW dex_trades_pool_mv $on_cluster
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
        swap_type as swap_type,
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
    
    CREATE MATERIALIZED VIEW dex_trades_factory_mv $on_cluster
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
        swap_type as swap_type,
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
    
    CREATE MATERIALIZED VIEW dex_trades_transaction_hash_mv $on_cluster
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
        swap_type as swap_type,
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
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    schema_template = """
    DROP VIEW dex_trades_token_mv $on_cluster;
    DROP VIEW dex_trades_wallet_mv $on_cluster;
    DROP VIEW dex_trades_pool_mv $on_cluster;
    DROP VIEW dex_trades_factory_mv $on_cluster;
    DROP VIEW dex_trades_transaction_hash_mv $on_cluster;
    
    ALTER TABLE dex_trades_token_wallet_pool_factory_hash $on_cluster DROP COLUMN swap_type;
    
    CREATE MATERIALIZED VIEW dex_trades_token_mv $on_cluster
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
        if statement.strip():
            op.execute(statement)
