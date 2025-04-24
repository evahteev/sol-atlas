CREATE TABLE engine.chainflow_events
(
    `id` Nullable(String),
    `rootProcessInstanceId` String,
    `processInstanceId` String,
    `executionId` String,
    `processDefinitionId` String,
    `processDefinitionKey` String,
    `eventType` Nullable(String),
    `startTime` UInt64,
    `endTime` Nullable(UInt64),
    `activityId` Nullable(String),
    `tenantId` Nullable(String),
    `state` Nullable(String),
    `rawData` String
)
ENGINE = MergeTree
ORDER BY (startTime, processDefinitionKey)
SETTINGS index_granularity = 8192

CREATE TABLE engine.chainflow_rabbitmq_events
(
    `rawData` String
)
ENGINE = RabbitMQ
SETTINGS rabbitmq_host_port = 'rabbitmq:5672',
    rabbitmq_vhost = '/',
    rabbitmq_exchange_name = 'engine',
    rabbitmq_exchange_type = 'direct',
    rabbitmq_routing_key_list = 'engine',
    rabbitmq_queue_settings_list = 'x-max-length-bytes=104857600,x-overflow=drop-head',
    rabbitmq_queue_base = 'engine.clickhouse',
    rabbitmq_max_block_size = 10485760,
    rabbitmq_flush_interval_ms = 10000,
    rabbitmq_skip_broken_messages = 99999999,
    rabbitmq_format = 'JSONAsString',
    rabbitmq_username = 'rabbitmq',
    rabbitmq_password = 'SomePassword123!'


CREATE MATERIALIZED VIEW engine.chainflow_rabbitmq_to_events TO engine.chainflow_events
(
    `id` Nullable(String),
    `rootProcessInstanceId` String,
    `processInstanceId` String,
    `executionId` String,
    `processDefinitionId` String,
    `processDefinitionKey` String,
    `eventType` Nullable(String),
    `startTime` UInt64,
    `endTime` Nullable(UInt64),
    `activityId` Nullable(String),
    `tenantId` Nullable(String),
    `state` Nullable(String),
    `rawData` String
)
AS SELECT
    JSONExtract(rawData, 'id', 'Nullable(String)') AS id,
    JSONExtractString(rawData, 'rootProcessInstanceId') AS rootProcessInstanceId,
    JSONExtractString(rawData, 'processInstanceId') AS processInstanceId,
    JSONExtractString(rawData, 'executionId') AS executionId,
    JSONExtractString(rawData, 'processDefinitionId') AS processDefinitionId,
    JSONExtractString(rawData, 'processDefinitionKey') AS processDefinitionKey,
    JSONExtract(rawData, 'eventType', 'Nullable(String)') AS eventType,
    JSONExtract(rawData, 'startTime', 'UInt64') AS startTime,
    JSONExtract(rawData, 'endTime', 'Nullable(UInt64)') AS endTime,
    JSONExtract(rawData, 'activityId', 'Nullable(String)') AS activityId,
    JSONExtract(rawData, 'tenantId', 'Nullable(String)') AS tenantId,
    JSONExtract(rawData, 'state', 'Nullable(String)') AS state,
    rawData AS rawData
FROM engine.chainflow_rabbitmq_events