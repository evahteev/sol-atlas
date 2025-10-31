"""
Token balance tracking tables and views.

Revision ID: a3b4c5d6e7f8
Revises: 695a31977b76
Create Date: 2025-01-02 15:30:27.000000
"""
import os
import string
from functools import cache

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'a3b4c5d6e7f8'
down_revision = '695a31977b76'
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
    connection = op.get_bind()
    
    # Part 1: Create balance tracking tables with TTL
    schema_template_increases = """
        CREATE TABLE IF NOT EXISTS token_balance_increases $on_cluster
        (
            token_address String,
            holder_address String,
            token_id Nullable(UInt256),
            amount UInt256,
            block_number UInt64,
            block_timestamp UInt32,
            token_standard LowCardinality(String),
            transaction_hash String,
            log_index UInt32
        )
        ENGINE = $replicatedMergeTree()
        ORDER BY (token_address, holder_address, coalesce(token_id, 0), block_number)
        TTL toDateTime(block_timestamp) + INTERVAL 90 DAY
    """
    
    schema_template_decreases = """
        CREATE TABLE IF NOT EXISTS token_balance_decreases $on_cluster
        (
            token_address String,
            holder_address String,
            token_id Nullable(UInt256),
            amount UInt256,
            block_number UInt64,
            block_timestamp UInt32,
            token_standard LowCardinality(String),
            transaction_hash String,
            log_index UInt32
        )
        ENGINE = $replicatedMergeTree()
        ORDER BY (token_address, holder_address, coalesce(token_id, 0), block_number)
        TTL toDateTime(block_timestamp) + INTERVAL 90 DAY
    """
    
    # Part 2: Create current balances table
    schema_template_current_balances = """
        CREATE TABLE IF NOT EXISTS current_token_balances $on_cluster
        (
            token_address String,
            holder_address String,
            token_id Nullable(UInt256),
            current_balance UInt256,
            last_updated_block UInt64,
            last_updated_timestamp UInt32,
            token_standard LowCardinality(String)
        )
        ENGINE = $replicatedReplacingMergeTree(last_updated_block)
        ORDER BY (token_address, holder_address, coalesce(token_id, 0))
        SETTINGS index_granularity = 8192
    """
    
    # Part 3: Create balance delta table to track changes from both sources
    schema_template_balance_delta = """
        CREATE TABLE IF NOT EXISTS token_balance_delta $on_cluster
        (
            token_address String,
            holder_address String,
            token_id Nullable(UInt256),
            token_standard LowCardinality(String),
            balance_delta Int256,
            block_number UInt64,
            block_timestamp UInt32
        )
        ENGINE = $replicatedSummingMergeTree(balance_delta)
        ORDER BY (token_address, holder_address, coalesce(token_id, 0))
    """
    
    # Part 4: Create materialized views for increases and decreases separately
    schema_template_mv_increases = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS token_balance_increases_mv $on_cluster
        TO token_balance_delta
        AS SELECT
            token_address,
            holder_address,
            token_id,
            token_standard,
            toInt256(amount) as balance_delta,
            block_number,
            block_timestamp
        FROM token_balance_increases
        WHERE holder_address != '0x0000000000000000000000000000000000000000'
    """
    
    schema_template_mv_decreases = """
        CREATE MATERIALIZED VIEW IF NOT EXISTS token_balance_decreases_mv $on_cluster
        TO token_balance_delta
        AS SELECT
            token_address,
            holder_address,
            token_id,
            token_standard,
            -toInt256(amount) as balance_delta,
            block_number,
            block_timestamp
        FROM token_balance_decreases
        WHERE holder_address != '0x0000000000000000000000000000000000000000'
    """
    
    # Part 5: Handle existing token_balances table and create views
    # First, rename existing token_balances table if it exists
    rename_existing_table = """
        RENAME TABLE IF EXISTS token_balances TO token_balances_legacy $on_cluster
    """
    
    # Then create the view
    view_token_balances = """
        CREATE VIEW IF NOT EXISTS token_balances $on_cluster AS
        SELECT
            token_address,
            token_standard,
            holder_address,
            max(block_number) as block_number,
            max(block_timestamp) as block_timestamp,
            greatest(0, sum(balance_delta)) as value,
            coalesce(token_id, 0) as token_id,
            '' as block_hash,
            0 as is_reorged
        FROM token_balance_delta
        GROUP BY token_address, holder_address, token_id, token_standard
        HAVING greatest(0, sum(balance_delta)) > 0
        ORDER BY token_address, holder_address, token_id
    """
    
    view_erc20_balances = """
        CREATE VIEW IF NOT EXISTS current_erc20_balances $on_cluster AS
        SELECT
            token_address,
            holder_address,
            value as current_balance,
            block_number as last_updated_block,
            block_timestamp as last_updated_timestamp
        FROM token_balances
        WHERE token_standard = 'ERC-20'
          AND value > 0
        ORDER BY token_address, current_balance DESC
    """
    
    view_nft_ownership = """
        CREATE VIEW IF NOT EXISTS current_nft_ownership $on_cluster AS
        SELECT
            token_address,
            holder_address,
            token_id,
            value as current_balance,
            block_number as last_updated_block,
            block_timestamp as last_updated_timestamp,
            token_standard
        FROM token_balances
        WHERE token_standard IN ('ERC-721', 'ERC-1155')
          AND token_id > 0
          AND value > 0
        ORDER BY token_address, token_id, current_balance DESC
    """
    
    view_token_supply = """
        CREATE VIEW IF NOT EXISTS token_supply_tracking $on_cluster AS
        SELECT
            token_address,
            holder_address,
            token_id,
            token_standard,
            value as balance,
            block_number as last_updated_block,
            block_timestamp as last_updated_timestamp
        FROM token_balances
        ORDER BY token_address, coalesce(token_id, 0), balance DESC
    """
    
    view_nft_stats = """
        CREATE VIEW IF NOT EXISTS nft_collection_stats $on_cluster AS
        SELECT
            token_address,
            token_standard,
            count(DISTINCT token_id) as unique_tokens,
            count(DISTINCT holder_address) as unique_holders,
            sum(current_balance) as total_supply
        FROM current_nft_ownership
        GROUP BY token_address, token_standard
        ORDER BY unique_holders DESC
    """
    
    # Configure replication settings
    if is_clickhouse_replicated():
        on_cluster = "ON CLUSTER '{cluster}'"
        replicated = "Replicated"
        replicatedMergeTree = "ReplicatedMergeTree"
        replicatedReplacingMergeTree = "ReplicatedReplacingMergeTree"
        replicatedSummingMergeTree = "ReplicatedSummingMergeTree"
    else:
        on_cluster = ""
        replicated = ""
        replicatedMergeTree = "MergeTree"
        replicatedReplacingMergeTree = "ReplacingMergeTree"
        replicatedSummingMergeTree = "SummingMergeTree"
    
    # Execute all statements
    templates = [
        schema_template_increases,
        schema_template_decreases,
        schema_template_current_balances,
        schema_template_balance_delta,
        schema_template_mv_increases,
        schema_template_mv_decreases,
        rename_existing_table,  # Rename existing table before creating view
        view_token_balances,
        view_erc20_balances,
        view_nft_ownership,
        view_token_supply,
        view_nft_stats
    ]
    
    for template in templates:
        sql = string.Template(template).substitute(
            on_cluster=on_cluster,
            replicated=replicated,
            replicatedMergeTree=replicatedMergeTree,
            replicatedReplacingMergeTree=replicatedReplacingMergeTree,
            replicatedSummingMergeTree=replicatedSummingMergeTree
        )
        statements = filter(None, map(str.strip, sql.split(";\n")))
        for statement in statements:
            op.execute(statement)


def downgrade() -> None:
    # Drop views first (in reverse order of creation)
    drop_views = [
        "DROP VIEW IF EXISTS nft_collection_stats $on_cluster",
        "DROP VIEW IF EXISTS token_supply_tracking $on_cluster",
        "DROP VIEW IF EXISTS current_nft_ownership $on_cluster",
        "DROP VIEW IF EXISTS current_erc20_balances $on_cluster",
        "DROP VIEW IF EXISTS token_balances $on_cluster",
        "DROP VIEW IF EXISTS token_balance_decreases_mv $on_cluster",
        "DROP VIEW IF EXISTS token_balance_increases_mv $on_cluster"
    ]
    
    # Restore original token_balances table if it was renamed
    restore_table = "RENAME TABLE IF EXISTS token_balances_legacy TO token_balances $on_cluster"
    
    # Drop tables
    drop_tables = [
        "DROP TABLE IF EXISTS token_balance_delta $on_cluster SYNC",
        "DROP TABLE IF EXISTS current_token_balances $on_cluster SYNC",
        "DROP TABLE IF EXISTS token_balance_decreases $on_cluster SYNC",
        "DROP TABLE IF EXISTS token_balance_increases $on_cluster SYNC"
    ]
    
    if is_clickhouse_replicated():
        on_cluster = "ON CLUSTER '{cluster}'"
    else:
        on_cluster = ""
    
    # Execute drops and restore
    for statement in drop_views:
        sql = string.Template(statement).substitute(on_cluster=on_cluster)
        op.execute(sql)
    
    # Restore original table after dropping the view
    sql = string.Template(restore_table).substitute(on_cluster=on_cluster)
    op.execute(sql)
    
    # Drop remaining objects
    for statement in drop_tables:
        sql = string.Template(statement).substitute(on_cluster=on_cluster)
        op.execute(sql) 