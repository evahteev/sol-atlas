"""
Create candles tables and mv.

Revision ID: 0b5f4dd31797
Revises: e3ce81fe0110
Create Date: 2024-01-26 18:38:24.339874
"""
import os
import string
from functools import cache

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = '0b5f4dd31797'
down_revision = 'e3ce81fe0110'
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
        CREATE TABLE `candles_1m` $on_cluster
        (
            timestamp     UInt64,
            token_address String CODEC(ZSTD(1)),
            pool_address String CODEC(ZSTD(1)),
            factory_address String CODEC(ZSTD(1)),
            c_s SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            o_s SimpleAggregateFunction(min, Tuple(UInt64, Float64)),
            h_s SimpleAggregateFunction(max, Float64),
            l_s SimpleAggregateFunction(min, Float64),
            c_n SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            o_n SimpleAggregateFunction(min, Tuple(UInt64, Float64)),
            h_n SimpleAggregateFunction(max, Float64),
            l_n SimpleAggregateFunction(min, Float64),
            v_s SimpleAggregateFunction(sum, Float64),
            v_n SimpleAggregateFunction(sum, Float64),
            liq_s SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            liq_n SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            tx_count SimpleAggregateFunction(sum, UInt64)
        )
            engine = ${replicated}AggregatingMergeTree${replication_path} PARTITION BY toYYYYMM(FROM_UNIXTIME(timestamp))
                ORDER BY (token_address, pool_address, timestamp)
                SETTINGS index_granularity = 8192;
        
        CREATE TABLE `candles_5m` $on_cluster
        (
            timestamp     UInt64,
            token_address String CODEC(ZSTD(1)),
            pool_address String CODEC(ZSTD(1)),
            factory_address String CODEC(ZSTD(1)),
            c_s SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            o_s SimpleAggregateFunction(min, Tuple(UInt64, Float64)),
            h_s SimpleAggregateFunction(max, Float64),
            l_s SimpleAggregateFunction(min, Float64),
            c_n SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            o_n SimpleAggregateFunction(min, Tuple(UInt64, Float64)),
            h_n SimpleAggregateFunction(max, Float64),
            l_n SimpleAggregateFunction(min, Float64),
            v_s SimpleAggregateFunction(sum, Float64),
            v_n SimpleAggregateFunction(sum, Float64),
            liq_s SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            liq_n SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            tx_count SimpleAggregateFunction(sum, UInt64)
        )
            engine = ${replicated}AggregatingMergeTree${replication_path} PARTITION BY toYYYYMM(FROM_UNIXTIME(timestamp))
                ORDER BY (token_address, pool_address, timestamp)
                SETTINGS index_granularity = 8192;
       
        CREATE TABLE `candles_1h` $on_cluster
        (
            timestamp     UInt64,
            token_address String CODEC(ZSTD(1)),
            pool_address String CODEC(ZSTD(1)),
            factory_address String CODEC(ZSTD(1)),
            c_s SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            o_s SimpleAggregateFunction(min, Tuple(UInt64, Float64)),
            h_s SimpleAggregateFunction(max, Float64),
            l_s SimpleAggregateFunction(min, Float64),
            c_n SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            o_n SimpleAggregateFunction(min, Tuple(UInt64, Float64)),
            h_n SimpleAggregateFunction(max, Float64),
            l_n SimpleAggregateFunction(min, Float64),
            v_s SimpleAggregateFunction(sum, Float64),
            v_n SimpleAggregateFunction(sum, Float64),
            liq_s SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            liq_n SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            tx_count SimpleAggregateFunction(sum, UInt64)
        )
            engine = ${replicated}AggregatingMergeTree${replication_path} PARTITION BY toYYYYMM(FROM_UNIXTIME(timestamp))
                ORDER BY (token_address, pool_address, timestamp)
                SETTINGS index_granularity = 8192; 
        
        CREATE TABLE `candles_1d` $on_cluster
        (
            timestamp     UInt64,
            token_address String,
            pool_address String,
            factory_address String,
            c_s SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            o_s SimpleAggregateFunction(min, Tuple(UInt64, Float64)),
            h_s SimpleAggregateFunction(max, Float64),
            l_s SimpleAggregateFunction(min, Float64),
            c_n SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            o_n SimpleAggregateFunction(min, Tuple(UInt64, Float64)),
            h_n SimpleAggregateFunction(max, Float64),
            l_n SimpleAggregateFunction(min, Float64),
            v_s SimpleAggregateFunction(sum, Float64),
            v_n SimpleAggregateFunction(sum, Float64),
            liq_s SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            liq_n SimpleAggregateFunction(max, Tuple(UInt64, Float64)),
            tx_count SimpleAggregateFunction(sum, UInt64)
        )
            engine = ${replicated}AggregatingMergeTree${replication_path} PARTITION BY toYYYYMM(FROM_UNIXTIME(timestamp))
                ORDER BY (token_address, pool_address, timestamp)
                SETTINGS index_granularity = 8192;
                
        
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

    clickhouse_replicated = (
        os.getenv('CLICKHOUSE_REPLICATED', '').lower() in ('true', '1')
        or op.get_bind().execute(text("SELECT count() FROM system.replicas")).scalar_one() > 0
    )
    on_cluster = os.getenv('ON_CLUSTER', '').lower() in ('true', '1')
    if on_cluster:
        on_cluster = "ON CLUSTER '{cluster}'"
    else:
        on_cluster = ""

    if clickhouse_replicated:
        sql = string.Template(schema_template).substitute(
            on_cluster=on_cluster,
            replicated="Replicated",
            replication_path = "('/clickhouse/tables/{database}/{shard}/{table}', '{replica}-{cluster}')",
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
    schema_template = """
                      DROP TABLE candles_1m $on_cluster SYNC;
                      DROP TABLE candles_5m $on_cluster SYNC;
                      DROP TABLE candles_1h $on_cluster SYNC;
                      DROP TABLE candles_1d $on_cluster SYNC;
                      DROP VIEW candles_1m_mv $on_cluster SYNC;
                      DROP VIEW candles_5m_mv $on_cluster SYNC;
                      DROP VIEW candles_1h_mv $on_cluster SYNC;
                      DROP VIEW candles_1d_mv $on_cluster SYNC;
                      """

    clickhouse_replicated = (
        os.getenv('CLICKHOUSE_REPLICATED', '').lower() in ('true', '1')
        or op.get_bind().execute(text("SELECT count() FROM system.replicas")).scalar_one() > 0
    )

    if clickhouse_replicated:
        sql = string.Template(schema_template).substitute(
            on_cluster="ON CLUSTER '{cluster}'",
            replicated="Replicated",
            replication_path = "('/clickhouse/tables/{database}/{shard}/{table}', '{replica}-{cluster}')",
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
