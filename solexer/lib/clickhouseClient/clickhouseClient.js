"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
exports.read = read;
exports.write = write;
exports.insert = insert;
exports.execute = execute;
const client_1 = require("@clickhouse/client");
const config_solana_1 = require("../config-solana");
const clickhouse = (0, client_1.createClient)({
    url: config_solana_1.CLICKHOUSE_CONFIG.url,
    username: config_solana_1.CLICKHOUSE_CONFIG.username,
    password: config_solana_1.CLICKHOUSE_CONFIG.password,
    database: config_solana_1.CLICKHOUSE_CONFIG.database,
    request_timeout: config_solana_1.CONFIG.CLICKHOUSE_TIMEOUT,
});
// Retry configuration
const MAX_RETRIES = config_solana_1.CONFIG.CLICKHOUSE_MAX_RETRIES;
const INITIAL_RETRY_DELAY = config_solana_1.CONFIG.CLICKHOUSE_RETRY_DELAY;
const MAX_RETRY_DELAY = config_solana_1.CONFIG.CLICKHOUSE_MAX_RETRY_DELAY;
exports.default = clickhouse;
// Helper function to implement retry logic with exponential backoff
async function withRetry(operation, operationName) {
    let lastError = null;
    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
        try {
            return await operation();
        }
        catch (error) {
            lastError = error;
            // Check if it's a timeout or connection error that we should retry
            const isRetryableError = error.message?.includes('Timeout') ||
                error.message?.includes('ECONNRESET') ||
                error.message?.includes('ECONNREFUSED') ||
                error.message?.includes('ETIMEDOUT') ||
                error.code === 'ECONNRESET' ||
                error.code === 'ECONNREFUSED' ||
                error.code === 'ETIMEDOUT' ||
                error.code === 'EPIPE';
            if (!isRetryableError || attempt === MAX_RETRIES) {
                throw error;
            }
            // Calculate delay with exponential backoff
            const delay = Math.min(INITIAL_RETRY_DELAY * Math.pow(2, attempt), MAX_RETRY_DELAY);
            console.warn(`${operationName} failed (attempt ${attempt + 1}/${MAX_RETRIES + 1}): ${error.message}. Retrying in ${delay}ms...`);
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
    throw lastError;
}
async function read(query) {
    return withRetry(async () => {
        const result = await clickhouse.query({
            query,
            format: 'JSONEachRow',
        });
        return await result.json();
    }, 'read');
}
async function write(query) {
    return withRetry(async () => {
        return await clickhouse.command({
            query,
        });
    }, 'write');
}
async function insert(table, rows) {
    if (!rows.length)
        return;
    return withRetry(async () => {
        return await clickhouse.insert({
            table,
            values: rows,
            format: 'JSONEachRow',
        });
    }, `insert into ${table}`);
}
async function execute(query) {
    return withRetry(async () => {
        return await clickhouse.command({ query });
    }, 'execute');
}
