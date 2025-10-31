"""
${message}.

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}
"""
import os
import string
from functools import cache

from alembic import op
${imports if imports else ""}
# revision identifiers, used by Alembic.
revision = ${repr(up_revision)}
down_revision = ${repr(down_revision)}
branch_labels = ${repr(branch_labels)}
depends_on = ${repr(depends_on)}


@cache
def is_clickhouse_replicated():
    if os.getenv('CLICKHOUSE_REPLICATED', '').lower() in ('true', '1'):
        return True

    result = op.get_bind().execute("SELECT count() FROM system.replicas")
    if result:
        return result.one()[0] > 0

    return False


def upgrade() -> None:
    schema_template = """
    CREATE TABLE example $on_cluster
    (
        `a` UInt64,
        `b` String,
        `version` UInt32,
    )
    ENGINE = ${"${replicated}"}ReplacingMergeTree(version)
    ORDER BY a
    """

    if is_clickhouse_replicated():
        on_cluster = "ON CLUSTER '${"{cluster}"}'"
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
    schema_template = "DROP TABLE example $on_cluster SYNC"

    if is_clickhouse_replicated():
        on_cluster = "ON CLUSTER '${"{cluster}"}'"
        replicated = "Replicated"
    else:
        on_cluster = ""
        replicated = ""

    _ = replicated

    sql = string.Template(schema_template).substitute(
        on_cluster=on_cluster,
    )

    op.execute(sql)
