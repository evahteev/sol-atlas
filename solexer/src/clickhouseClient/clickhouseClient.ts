import {createClient} from '@clickhouse/client';
import {CLICKHOUSE_CONFIG, CONFIG} from '../config-solana';

const clickhouse = createClient({
    url: CLICKHOUSE_CONFIG.url,
    username: CLICKHOUSE_CONFIG.username,
    password: CLICKHOUSE_CONFIG.password,
    database: CLICKHOUSE_CONFIG.database,
    request_timeout: CONFIG.CLICKHOUSE_TIMEOUT,
});

// Retry configuration
const MAX_RETRIES = CONFIG.CLICKHOUSE_MAX_RETRIES;
const INITIAL_RETRY_DELAY = CONFIG.CLICKHOUSE_RETRY_DELAY;
const MAX_RETRY_DELAY = CONFIG.CLICKHOUSE_MAX_RETRY_DELAY;

export default clickhouse;

// Helper function to implement retry logic with exponential backoff
async function withRetry<T>(
    operation: () => Promise<T>,
    operationName: string
): Promise<T> {
    let lastError: Error | null = null;
    
    for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
        try {
            return await operation();
        } catch (error: any) {
            lastError = error;
            
            // Check if it's a timeout or connection error that we should retry
            const isRetryableError = 
                error.message?.includes('Timeout') ||
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
            const delay = Math.min(
                INITIAL_RETRY_DELAY * Math.pow(2, attempt),
                MAX_RETRY_DELAY
            );
            
            console.warn(
                `${operationName} failed (attempt ${attempt + 1}/${MAX_RETRIES + 1}): ${error.message}. Retrying in ${delay}ms...`
            );
            
            await new Promise(resolve => setTimeout(resolve, delay));
        }
    }
    
    throw lastError;
}

export async function read(query: string) {
    return withRetry(async () => {
    const result = await clickhouse.query({
        query,
        format: 'JSONEachRow',
    });
    return await result.json();
    }, 'read');
}

export async function write(query: string) {
    return withRetry(async () => {
    return await clickhouse.command({
        query,
    });
    }, 'write');
}

export async function insert(table: string, rows: any[]) {
    if (!rows.length) return;
    
    return withRetry(async () => {
    return await clickhouse.insert({
        table,
        values: rows,
        format: 'JSONEachRow',
    });
    }, `insert into ${table}`);
}

export async function execute(query: string) {
    return withRetry(async () => {
    return await clickhouse.command({ query });
    }, 'execute');
}
