"""Add swap_type column to dex_trades table

Revision ID: add_swap_type_column
Revises: e53d5b572cab
Create Date: 2025-01-05 12:03:00.000000

"""
from alembic import op
from sqlalchemy import text
import sqlalchemy as sa
import os
import string
from functools import cache


# revision identifiers, used by Alembic.
revision = '1757006980_add_swap_type_column'
down_revision = 'a3b4c5d6e7f8'
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
    ALTER TABLE dex_trades $on_cluster ADD COLUMN swap_type String DEFAULT 'buy' CODEC(ZSTD(1)) AFTER transaction_type;
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
        op.execute(statement)


def downgrade() -> None:
    schema_template = """
    ALTER TABLE dex_trades $on_cluster DROP COLUMN swap_type;
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
        op.execute(statement)
