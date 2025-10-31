"""Add Solana AMM support and metadata table

Revision ID: 1757008000_add_solana_amm_types
Revises: 1757007000_update_materialized_views_swap_type
Create Date: 2025-01-05 12:00:00.000000

"""
from alembic import op
from sqlalchemy import text
import sqlalchemy as sa
import os
import string
from functools import cache


# revision identifiers, used by Alembic.
revision = '1757008000_add_solana_amm_types'
down_revision = '1757007000_update_materialized_views_swap_type'
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
    Add support for Solana DEX protocols.
    
    Notes:
    - The dex_trades.amm column is already a String type, so it can accept new values
      like 'jupiter_v6', 'jupiter_v4', 'pump' without schema changes
    - This migration creates an optional metadata table for Solana-specific fields
    - Solana addresses are base58-encoded (43-44 chars) vs EVM hex (42 chars with 0x)
    - Solana uses 'slot' instead of 'block_number', but we store it in block_number field
    - Transaction signatures in Solana are stored in transaction_hash field (base58)
    """
    schema_template = """
    CREATE TABLE IF NOT EXISTS solana_trade_metadata $on_cluster (
        transaction_hash String,
        slot UInt64,
        instruction_index UInt32,
        inner_instruction_index Nullable(UInt32),
        
        -- Pump.fun specific fields
        virtual_sol_reserves Nullable(String),
        virtual_token_reserves Nullable(String),
        fee_basis_points Nullable(UInt64),
        creator_fee_basis_points Nullable(UInt64),
        
        -- Timestamps
        created_at DateTime DEFAULT now()
    ) ENGINE = ${replicated}MergeTree${replication_path}
    ORDER BY (transaction_hash)
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
    Remove Solana-specific metadata table.
    Note: We don't remove AMM type values from dex_trades as it's a String field.
    """
    schema_template = """
    DROP TABLE IF EXISTS solana_trade_metadata $on_cluster SYNC;
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

