"""Add solana_indexer_state table for tracking processing progress

Revision ID: 1757009000_add_solana_indexer_state
Revises: 1757008000_add_solana_amm_types
Create Date: 2025-01-05 14:00:00.000000

This migration adds a state table to track the latest processed block height
for the Solana indexer. This allows resuming from the last processed block
instead of relying solely on environment variables.
"""
from alembic import op
from sqlalchemy import text
import sqlalchemy as sa
import os
import string
from functools import cache


# revision identifiers, used by Alembic.
revision = '1757009000_add_solana_indexer_state'
down_revision = '1757008000_add_solana_amm_types'
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
    """
    Create a state table to track indexer progress.
    
    This table stores key-value pairs for indexer state:
    - 'last_processed_block': The latest block height successfully processed
    - Can be extended with other state keys as needed
    
    Using ReplacingMergeTree to allow updates (last row with same key wins).
    """
    schema_template = """
    CREATE TABLE IF NOT EXISTS solana_indexer_state $on_cluster (
        state_key String,
        state_value String,
        chain String DEFAULT 'solana-mainnet',
        updated_at DateTime DEFAULT now(),
        version UInt64 DEFAULT 1
    ) ENGINE = ${replicated}ReplacingMergeTree${replication_path}(version)
    ORDER BY (chain, state_key)
    SETTINGS index_granularity = 8192;
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

    sql = string.Template(schema_template).substitute(
        on_cluster=on_cluster,
        replicated=replicated,
        replication_path=replication_path
    )
    statements = filter(None, map(str.strip, sql.split(";\n")))
    for statement in statements:
        if statement.strip():
            op.execute(statement)


def downgrade() -> None:
    """
    Remove the state table.
    """
    schema_template = """
    DROP TABLE IF EXISTS solana_indexer_state $on_cluster SYNC;
    """
    
    on_cluster = os.getenv('ON_CLUSTER', '').lower() in ('true', '1')
    if on_cluster:
        on_cluster = "ON CLUSTER '{cluster}'"
    else:
        on_cluster = ""

    sql = string.Template(schema_template).substitute(
        on_cluster=on_cluster,
    )
    statements = filter(None, map(str.strip, sql.split(";\n")))
    for statement in statements:
        if statement.strip():
            op.execute(statement)

