"""
fix candles material views.

Revision ID: e4c59630a7af
Revises: e63032f915ee
Create Date: 2024-05-23 14:44:23.050483
"""
import os
import string
from functools import cache

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'e4c59630a7af'
down_revision = 'e63032f915ee'
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
        DROP VIEW candles_1m_mv $on_cluster SYNC;
        DROP VIEW candles_5m_mv $on_cluster SYNC;
        DROP VIEW candles_1h_mv $on_cluster SYNC;
        DROP VIEW candles_1d_mv $on_cluster SYNC;
        
        CREATE MATERIALIZED VIEW `candles_1m_mv` $on_cluster TO `candles_1m`
        (
            `timestamp` UInt64,
            `token_address` String,
            `pool_address` String,
            `factory_address` String,
            `c_s` Tuple(UInt64, Float64),
            `o_s` Tuple(UInt64, Float64),
            `h_s` Float64,
            `l_s` Float64,
            `c_n` Tuple(UInt64, Float64),
            `o_n` Tuple(UInt64, Float64),
            `h_n` Float64,
            `l_n` Float64,
            `v_s` Float64,
            `v_n` Float64,
            `liq_s` Float64,
            `liq_n` Float64,
            `tx_count` UInt64
        ) AS
        SELECT
            toStartOfMinute(FROM_UNIXTIME(block_timestamp)) AS timestamp,
            tokens_data.1 AS token_address,
            pool_address AS pool_address,
            factory_address AS factory_address,
            max((block_timestamp, tokens_data.2)) as c_s,
            min((block_timestamp, tokens_data.2)) as o_s,
            max(tokens_data.2) as h_s,
            min(tokens_data.2) as l_s,
            max((block_timestamp, tokens_data.3)) as c_n,
            min((block_timestamp, tokens_data.3)) as o_n,
            max(tokens_data.3) as h_n,
            min(tokens_data.3) as l_n,
            sum(abs(tokens_data.4) * tokens_data.2) as v_s,
            sum(abs(tokens_data.4) * tokens_data.3) as v_n,
            max((block_timestamp, tokens_data.5 * tokens_data.2)) as liq_s,
            max((block_timestamp, tokens_data.5 * tokens_data.3)) as liq_n,
            count(DISTINCT swap_id) as tx_count
        FROM (
                 SELECT arrayJoin(arrayZip(token_addresses,
                                           arrayMap(i -> if(i <= length(prices_stable), prices_stable[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(prices_native), prices_native[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(amounts), amounts[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(reserves), reserves[i], 0), arrayEnumerate(token_addresses))
                                  )) as tokens_data,
                        pool_address                                        AS pool_address,
                        factory_address                                     AS factory_address,
                        block_timestamp                                     AS block_timestamp,
                        concat(transaction_hash, toString(log_index))       AS swap_id
                 FROM dex_trades
                 WHERE transaction_type = 'swap'
                 )
        WHERE tokens_data.2 > 0
        GROUP BY token_address, pool_address, timestamp, factory_address;
        
        CREATE MATERIALIZED VIEW `candles_5m_mv` $on_cluster TO `candles_5m`
        (
            `timestamp` UInt64,
            `token_address` String,
            `pool_address` String,
            `factory_address` String,
            `c_s` Tuple(UInt64, Float64),
            `o_s` Tuple(UInt64, Float64),
            `h_s` Float64,
            `l_s` Float64,
            `c_n` Tuple(UInt64, Float64),
            `o_n` Tuple(UInt64, Float64),
            `h_n` Float64,
            `l_n` Float64,
            `v_s` Float64,
            `v_n` Float64,
            `liq_s` Float64,
            `liq_n` Float64,
            `tx_count` UInt64
        ) AS
        SELECT
            toStartOfFiveMinute(FROM_UNIXTIME(block_timestamp)) AS timestamp,
            tokens_data.1 AS token_address,
            pool_address AS pool_address,
            factory_address AS factory_address,
            max((block_timestamp, tokens_data.2)) as c_s,
            min((block_timestamp, tokens_data.2)) as o_s,
            max(tokens_data.2) as h_s,
            min(tokens_data.2) as l_s,
            max((block_timestamp, tokens_data.3)) as c_n,
            min((block_timestamp, tokens_data.3)) as o_n,
            max(tokens_data.3) as h_n,
            min(tokens_data.3) as l_n,
            sum(abs(tokens_data.4) * tokens_data.2) as v_s,
            sum(abs(tokens_data.4) * tokens_data.3) as v_n,
            max((block_timestamp, tokens_data.5 * tokens_data.2)) as liq_s,
            max((block_timestamp, tokens_data.5 * tokens_data.3)) as liq_n,
            count(DISTINCT swap_id) as tx_count
        FROM (
                 SELECT arrayJoin(arrayZip(token_addresses,
                                           arrayMap(i -> if(i <= length(prices_stable), prices_stable[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(prices_native), prices_native[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(amounts), amounts[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(reserves), reserves[i], 0), arrayEnumerate(token_addresses))
                                  )) as tokens_data,
                        pool_address                                        AS pool_address,
                        factory_address                                     AS factory_address,
                        block_timestamp                                     AS block_timestamp,
                        concat(transaction_hash, toString(log_index))       AS swap_id
                 FROM dex_trades
                 WHERE transaction_type = 'swap'
                 )
        WHERE tokens_data.2 > 0
        GROUP BY token_address, pool_address, timestamp, factory_address;
        
        CREATE MATERIALIZED VIEW `candles_1h_mv` $on_cluster TO `candles_1h`
        (
            `timestamp` UInt64,
            `token_address` String,
            `pool_address` String,
            `factory_address` String,
            `c_s` Tuple(UInt64, Float64),
            `o_s` Tuple(UInt64, Float64),
            `h_s` Float64,
            `l_s` Float64,
            `c_n` Tuple(UInt64, Float64),
            `o_n` Tuple(UInt64, Float64),
            `h_n` Float64,
            `l_n` Float64,
            `v_s` Float64,
            `v_n` Float64,
            `liq_s` Float64,
            `liq_n` Float64,
            `tx_count` UInt64
        ) AS
        SELECT
            toStartOfHour(FROM_UNIXTIME(block_timestamp)) AS timestamp,
            tokens_data.1 AS token_address,
            pool_address AS pool_address,
            factory_address AS factory_address,
            max((block_timestamp, tokens_data.2)) as c_s,
            min((block_timestamp, tokens_data.2)) as o_s,
            max(tokens_data.2) as h_s,
            min(tokens_data.2) as l_s,
            max((block_timestamp, tokens_data.3)) as c_n,
            min((block_timestamp, tokens_data.3)) as o_n,
            max(tokens_data.3) as h_n,
            min(tokens_data.3) as l_n,
            sum(abs(tokens_data.4) * tokens_data.2) as v_s,
            sum(abs(tokens_data.4) * tokens_data.3) as v_n,
            max((block_timestamp, tokens_data.5 * tokens_data.2)) as liq_s,
            max((block_timestamp, tokens_data.5 * tokens_data.3)) as liq_n,
            count(DISTINCT swap_id) as tx_count
        FROM (
                 SELECT arrayJoin(arrayZip(token_addresses,
                                           arrayMap(i -> if(i <= length(prices_stable), prices_stable[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(prices_native), prices_native[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(amounts), amounts[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(reserves), reserves[i], 0), arrayEnumerate(token_addresses))
                                  )) as tokens_data,
                        pool_address                                        AS pool_address,
                        factory_address                                     AS factory_address,
                        block_timestamp                                     AS block_timestamp,
                        concat(transaction_hash, toString(log_index))       AS swap_id
                 FROM dex_trades
                 WHERE transaction_type = 'swap'
                 )
        WHERE tokens_data.2 > 0
        GROUP BY token_address, pool_address, timestamp, factory_address;
        
        CREATE MATERIALIZED VIEW `candles_1d_mv` $on_cluster TO `candles_1d`
        (
            `timestamp` UInt64,
            `token_address` String,
            `pool_address` String,
            `factory_address` String,
            `c_s` Tuple(UInt64, Float64),
            `o_s` Tuple(UInt64, Float64),
            `h_s` Float64,
            `l_s` Float64,
            `c_n` Tuple(UInt64, Float64),
            `o_n` Tuple(UInt64, Float64),
            `h_n` Float64,
            `l_n` Float64,
            `v_s` Float64,
            `v_n` Float64,
            `liq_s` Float64,
            `liq_n` Float64,
            `tx_count` UInt64
        ) AS
        SELECT
            toStartOfDay(FROM_UNIXTIME(block_timestamp)) AS timestamp,
            tokens_data.1 AS token_address,
            pool_address AS pool_address,
            factory_address AS factory_address,
            max((block_timestamp, tokens_data.2)) as c_s,
            min((block_timestamp, tokens_data.2)) as o_s,
            max(tokens_data.2) as h_s,
            min(tokens_data.2) as l_s,
            max((block_timestamp, tokens_data.3)) as c_n,
            min((block_timestamp, tokens_data.3)) as o_n,
            max(tokens_data.3) as h_n,
            min(tokens_data.3) as l_n,
            sum(abs(tokens_data.4) * tokens_data.2) as v_s,
            sum(abs(tokens_data.4) * tokens_data.3) as v_n,
            max((block_timestamp, tokens_data.5 * tokens_data.2)) as liq_s,
            max((block_timestamp, tokens_data.5 * tokens_data.3)) as liq_n,
            count(DISTINCT swap_id) as tx_count
        FROM (
                 SELECT arrayJoin(arrayZip(token_addresses,
                                           arrayMap(i -> if(i <= length(prices_stable), prices_stable[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(prices_native), prices_native[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(amounts), amounts[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(reserves), reserves[i], 0), arrayEnumerate(token_addresses))
                                  )) as tokens_data,
                        pool_address                                        AS pool_address,
                        factory_address                                     AS factory_address,
                        block_timestamp                                     AS block_timestamp,
                        concat(transaction_hash, toString(log_index))       AS swap_id
                 FROM dex_trades
                 WHERE transaction_type = 'swap'
                 )
        WHERE tokens_data.2 > 0
        GROUP BY token_address, pool_address, timestamp, factory_address;
        
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
        DROP VIEW candles_1m_mv $on_cluster SYNC;
        DROP VIEW candles_5m_mv $on_cluster SYNC;
        DROP VIEW candles_1h_mv $on_cluster SYNC;
        DROP VIEW candles_1d_mv $on_cluster SYNC;
    
        CREATE MATERIALIZED VIEW `candles_1m_mv` $on_cluster TO `candles_1m`
        (
            `timestamp` UInt64,
            `token_address` String,
            `pool_address` String,
            `factory_address` String,
            `c_s` Tuple(UInt64, Float64),
            `o_s` Tuple(UInt64, Float64),
            `h_s` Float64,
            `l_s` Float64,
            `c_n` Tuple(UInt64, Float64),
            `o_n` Tuple(UInt64, Float64),
            `h_n` Float64,
            `l_n` Float64,
            `v_s` Float64,
            `v_n` Float64,
            `liq_s` Float64,
            `liq_n` Float64,
            `tx_count` UInt64
        ) AS
        SELECT
            toStartOfMinute(FROM_UNIXTIME(block_timestamp)) AS timestamp,
            tokens_data.1 AS token_address,
            pool_address AS pool_address,
            factory_address AS factory_address,
            max((block_timestamp, tokens_data.2)) as c_s,
            min((block_timestamp, tokens_data.2)) as o_s,
            max(tokens_data.2) as h_s,
            min(tokens_data.2) as l_s,
            max((block_timestamp, tokens_data.3)) as c_n,
            min((block_timestamp, tokens_data.3)) as o_n,
            max(tokens_data.3) as h_n,
            min(tokens_data.3) as l_n,
            sum(abs(tokens_data.4) * tokens_data.2) as v_s,
            sum(abs(tokens_data.4) * tokens_data.3) as v_n,
            max((block_timestamp, tokens_data.5 * tokens_data.2)) as liq_s,
            max((block_timestamp, tokens_data.5 * tokens_data.3)) as liq_n,
            count(DISTINCT swap_id) as tx_count
        FROM (
                 SELECT arrayJoin(arrayZip(token_addresses,
                                           arrayMap(i -> if(i <= length(prices_stable), prices_stable[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(prices_native), prices_native[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(amounts), amounts[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(reserves), reserves[i], 0), arrayEnumerate(token_addresses))
                                  )) as tokens_data,
                        pool_address                                        AS pool_address,
                        factory_address                                     AS factory_address,
                        block_timestamp                                     AS block_timestamp,
                        concat(transaction_hash, toString(log_index))       AS swap_id
                 FROM dex_trades
                 WHERE transaction_type = 'swap'
                 )
        WHERE tokens_data.2 > 0 AND tokens_data.3 > 0
        GROUP BY token_address, pool_address, timestamp, factory_address;
        
        CREATE MATERIALIZED VIEW `candles_5m_mv` $on_cluster TO `candles_5m`
        (
            `timestamp` UInt64,
            `token_address` String,
            `pool_address` String,
            `factory_address` String,
            `c_s` Tuple(UInt64, Float64),
            `o_s` Tuple(UInt64, Float64),
            `h_s` Float64,
            `l_s` Float64,
            `c_n` Tuple(UInt64, Float64),
            `o_n` Tuple(UInt64, Float64),
            `h_n` Float64,
            `l_n` Float64,
            `v_s` Float64,
            `v_n` Float64,
            `liq_s` Float64,
            `liq_n` Float64,
            `tx_count` UInt64
        ) AS
        SELECT
            toStartOfFiveMinute(FROM_UNIXTIME(block_timestamp)) AS timestamp,
            tokens_data.1 AS token_address,
            pool_address AS pool_address,
            factory_address AS factory_address,
            max((block_timestamp, tokens_data.2)) as c_s,
            min((block_timestamp, tokens_data.2)) as o_s,
            max(tokens_data.2) as h_s,
            min(tokens_data.2) as l_s,
            max((block_timestamp, tokens_data.3)) as c_n,
            min((block_timestamp, tokens_data.3)) as o_n,
            max(tokens_data.3) as h_n,
            min(tokens_data.3) as l_n,
            sum(abs(tokens_data.4) * tokens_data.2) as v_s,
            sum(abs(tokens_data.4) * tokens_data.3) as v_n,
            max((block_timestamp, tokens_data.5 * tokens_data.2)) as liq_s,
            max((block_timestamp, tokens_data.5 * tokens_data.3)) as liq_n,
            count(DISTINCT swap_id) as tx_count
        FROM (
                 SELECT arrayJoin(arrayZip(token_addresses,
                                           arrayMap(i -> if(i <= length(prices_stable), prices_stable[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(prices_native), prices_native[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(amounts), amounts[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(reserves), reserves[i], 0), arrayEnumerate(token_addresses))
                                  )) as tokens_data,
                        pool_address                                        AS pool_address,
                        factory_address                                     AS factory_address,
                        block_timestamp                                     AS block_timestamp,
                        concat(transaction_hash, toString(log_index))       AS swap_id
                 FROM dex_trades
                 WHERE transaction_type = 'swap'
                 )
        WHERE tokens_data.2 > 0 AND tokens_data.3 > 0
        GROUP BY token_address, pool_address, timestamp, factory_address;
        
        CREATE MATERIALIZED VIEW `candles_1h_mv` $on_cluster TO `candles_1h`
        (
            `timestamp` UInt64,
            `token_address` String,
            `pool_address` String,
            `factory_address` String,
            `c_s` Tuple(UInt64, Float64),
            `o_s` Tuple(UInt64, Float64),
            `h_s` Float64,
            `l_s` Float64,
            `c_n` Tuple(UInt64, Float64),
            `o_n` Tuple(UInt64, Float64),
            `h_n` Float64,
            `l_n` Float64,
            `v_s` Float64,
            `v_n` Float64,
            `liq_s` Float64,
            `liq_n` Float64,
            `tx_count` UInt64
        ) AS
        SELECT
            toStartOfHour(FROM_UNIXTIME(block_timestamp)) AS timestamp,
            tokens_data.1 AS token_address,
            pool_address AS pool_address,
            factory_address AS factory_address,
            max((block_timestamp, tokens_data.2)) as c_s,
            min((block_timestamp, tokens_data.2)) as o_s,
            max(tokens_data.2) as h_s,
            min(tokens_data.2) as l_s,
            max((block_timestamp, tokens_data.3)) as c_n,
            min((block_timestamp, tokens_data.3)) as o_n,
            max(tokens_data.3) as h_n,
            min(tokens_data.3) as l_n,
            sum(abs(tokens_data.4) * tokens_data.2) as v_s,
            sum(abs(tokens_data.4) * tokens_data.3) as v_n,
            max((block_timestamp, tokens_data.5 * tokens_data.2)) as liq_s,
            max((block_timestamp, tokens_data.5 * tokens_data.3)) as liq_n,
            count(DISTINCT swap_id) as tx_count
        FROM (
                 SELECT arrayJoin(arrayZip(token_addresses,
                                           arrayMap(i -> if(i <= length(prices_stable), prices_stable[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(prices_native), prices_native[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(amounts), amounts[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(reserves), reserves[i], 0), arrayEnumerate(token_addresses))
                                  )) as tokens_data,
                        pool_address                                        AS pool_address,
                        factory_address                                     AS factory_address,
                        block_timestamp                                     AS block_timestamp,
                        concat(transaction_hash, toString(log_index))       AS swap_id
                 FROM dex_trades
                 WHERE transaction_type = 'swap'
                 )
        WHERE tokens_data.2 > 0 AND tokens_data.3 > 0
        GROUP BY token_address, pool_address, timestamp, factory_address;
        
        CREATE MATERIALIZED VIEW `candles_1d_mv` $on_cluster TO `candles_1d`
        (
            `timestamp` UInt64,
            `token_address` String,
            `pool_address` String,
            `factory_address` String,
            `c_s` Tuple(UInt64, Float64),
            `o_s` Tuple(UInt64, Float64),
            `h_s` Float64,
            `l_s` Float64,
            `c_n` Tuple(UInt64, Float64),
            `o_n` Tuple(UInt64, Float64),
            `h_n` Float64,
            `l_n` Float64,
            `v_s` Float64,
            `v_n` Float64,
            `liq_s` Float64,
            `liq_n` Float64,
            `tx_count` UInt64
        ) AS
        SELECT
            toStartOfDay(FROM_UNIXTIME(block_timestamp)) AS timestamp,
            tokens_data.1 AS token_address,
            pool_address AS pool_address,
            factory_address AS factory_address,
            max((block_timestamp, tokens_data.2)) as c_s,
            min((block_timestamp, tokens_data.2)) as o_s,
            max(tokens_data.2) as h_s,
            min(tokens_data.2) as l_s,
            max((block_timestamp, tokens_data.3)) as c_n,
            min((block_timestamp, tokens_data.3)) as o_n,
            max(tokens_data.3) as h_n,
            min(tokens_data.3) as l_n,
            sum(abs(tokens_data.4) * tokens_data.2) as v_s,
            sum(abs(tokens_data.4) * tokens_data.3) as v_n,
            max((block_timestamp, tokens_data.5 * tokens_data.2)) as liq_s,
            max((block_timestamp, tokens_data.5 * tokens_data.3)) as liq_n,
            count(DISTINCT swap_id) as tx_count
        FROM (
                 SELECT arrayJoin(arrayZip(token_addresses,
                                           arrayMap(i -> if(i <= length(prices_stable), prices_stable[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(prices_native), prices_native[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(amounts), amounts[i], 0), arrayEnumerate(token_addresses)),
                                           arrayMap(i -> if(i <= length(reserves), reserves[i], 0), arrayEnumerate(token_addresses))
                                  )) as tokens_data,
                        pool_address                                        AS pool_address,
                        factory_address                                     AS factory_address,
                        block_timestamp                                     AS block_timestamp,
                        concat(transaction_hash, toString(log_index))       AS swap_id
                 FROM dex_trades
                 WHERE transaction_type = 'swap'
                 )
        WHERE tokens_data.2 > 0 AND tokens_data.3 > 0
        GROUP BY token_address, pool_address, timestamp, factory_address;
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
