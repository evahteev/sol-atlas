"""
Create tokens dict.

Revision ID: 695a31977b76
Revises: e4c59630a7af
Create Date: 2024-08-08 15:06:11.268330
"""
import os
import string
from functools import cache

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '695a31977b76'
down_revision = 'e4c59630a7af'
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
    db_query = connection.execute(text('SELECT currentDatabase()'))
    db_name = db_query.scalar()
    schema_template = f"""
        CREATE DICTIONARY tokens_dict $on_cluster
        (
            `address`      String,
            `name`         String,
            `symbol`       String,
            `decimals`     UInt8,
            `total_supply` UInt256
        )
        PRIMARY KEY address
        SOURCE(CLICKHOUSE(HOST 'localhost' PORT 9000 DATABASE '{db_name}' TABLE 'tokens'))
        LAYOUT(COMPLEX_KEY_DIRECT())
    """

    if is_clickhouse_replicated():
        on_cluster = "ON CLUSTER '{cluster}'"
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
    schema_template = "DROP DICTIONARY tokens_dict $on_cluster SYNC"

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

    op.execute(sql)
