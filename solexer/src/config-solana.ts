/**
 * Solana Indexer Configuration
 * 
 * Configuration for Solana blockchain indexing.
 * Based on: workdir/plan_docs/env_configuration.md
 */

import { config } from 'dotenv';
import * as path from 'path';

// Load from .env.solana if it exists, otherwise fall back to .env
config({ path: path.resolve(process.cwd(), '.env.solana') });
// Also load .env as fallback for shared variables
config();

/**
 * Solana-specific configuration
 */
export const CONFIG_SOLANA = {
    // Network configuration
    RPC_URL: process.env.RPC_URL || process.env.SOLANA_RPC_URL || process.env.SOLANA_RPC_ENDPOINT || 'https://api.mainnet-beta.solana.com',
    RPC_ENDPOINT: process.env.SOLANA_RPC_ENDPOINT || process.env.SOLANA_RPC_URL || process.env.RPC_URL || 'https://api.mainnet-beta.solana.com',
    SOLANA_RPC_URL: process.env.SOLANA_RPC_URL || process.env.RPC_URL || 'https://api.mainnet-beta.solana.com',
    RPC_RATE_LIMIT: process.env.SOLANA_RPC_RATE_LIMIT 
        ? parseInt(process.env.SOLANA_RPC_RATE_LIMIT) 
        : 10,
    
    // Subsquid/SQD configuration
    // NOTE: Check SOLANA_GATEWAY_URL first to avoid picking up EVM's GATEWAY_URL!
    // Default to Subsquid v2 archive (free, public access)
    GATEWAY_URL: process.env.SOLANA_GATEWAY_URL || process.env.GATEWAY_URL || 'https://v2.archive.subsquid.io/network/solana-mainnet',
    SQD_TOKEN: process.env.SQD_TOKEN || '',
    
    // ClickHouse configuration
    CLICKHOUSE_HOST: process.env.CLICKHOUSE_HOST || 'http://localhost:8123',
    CLICKHOUSE_USER: process.env.CLICKHOUSE_USER || 'default',
    CLICKHOUSE_PASSWORD: process.env.CLICKHOUSE_PASSWORD || 'PASS',
    CLICKHOUSE_DATABASE: process.env.CLICKHOUSE_DATABASE || 'base',
    
    // Chain configuration
    CHAIN_ID: process.env.SOLANA_CHAIN_ID || 'solana-mainnet',
    // IMPORTANT: Subsquid's .setBlockRange() uses BLOCK HEIGHT, not SLOT!
    // Block height = number of actual produced blocks (skips empty slots)
    // For Solana, height is typically ~22M less than slot number
    // 
    // Use SOLANA_START_HEIGHT if you know the exact height
    // Or use SOLANA_START_SLOT and we'll use it as-is (understanding it's actually a height)
    START_HEIGHT: process.env.SOLANA_START_HEIGHT || process.env.SOLANA_START_SLOT || process.env.START_BLOCK
        ? parseInt(process.env.SOLANA_START_HEIGHT || process.env.SOLANA_START_SLOT || process.env.START_BLOCK!) 
        : 250000000,
    END_HEIGHT: process.env.SOLANA_END_HEIGHT || process.env.SOLANA_END_SLOT || process.env.END_BLOCK
        ? parseInt(process.env.SOLANA_END_HEIGHT || process.env.SOLANA_END_SLOT || process.env.END_BLOCK!) 
        : undefined,
    BATCH_SIZE: process.env.SOLANA_BATCH_SIZE || process.env.BATCH_SIZE
        ? parseInt(process.env.SOLANA_BATCH_SIZE || process.env.BATCH_SIZE!) 
        : 100,
    
    // Program IDs (can be overridden in .env)
    JUPITER_V6_PROGRAM_ID: process.env.JUPITER_V6_PROGRAM_ID || 'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4',
    JUPITER_V4_PROGRAM_ID: process.env.JUPITER_V4_PROGRAM_ID || 'JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB',
    PUMP_PROGRAM_ID: process.env.PUMP_PROGRAM_ID || '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P',
    
    // Reference tokens
    SOLANA_NATIVE_TOKEN_ADDRESS: process.env.SOLANA_NATIVE_TOKEN_ADDRESS || 'So11111111111111111111111111111111111111112',
    SOLANA_USDC_ADDRESS: process.env.SOLANA_USDC_ADDRESS || 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',
    
    // Output configuration
    OUTPUT: process.env.SOLANA_OUTPUT || 'clickhouse+http://default:@localhost:8123/solana_indexer',
    
    // Entity types
    ENTITY_TYPES: process.env.SOLANA_ENTITY_TYPES || 'dex_trade,dex_pool',
    SAVING_ENTITIES: process.env.SOLANA_SAVING_ENTITIES || 'dex_trade',
    
    // Testing configuration
    TEST_JUPITER_TX: process.env.TEST_JUPITER_TX || '',
    TEST_PUMP_BUY_TX: process.env.TEST_PUMP_BUY_TX || '',
    TEST_PUMP_SELL_TX: process.env.TEST_PUMP_SELL_TX || '',
} as const;

/**
 * Log Solana configuration
 */
export function logSolanaConfiguration(): void {
    console.log('🟣 Solana Indexer Configuration:');
    console.log('');
    console.log('Network:');
    console.log(`  Chain ID: ${CONFIG_SOLANA.CHAIN_ID}`);
    console.log(`  RPC URL: ${CONFIG_SOLANA.RPC_URL}`);
    console.log(`  RPC Rate Limit: ${CONFIG_SOLANA.RPC_RATE_LIMIT} req/s`);
    console.log(`  Gateway URL: ${CONFIG_SOLANA.GATEWAY_URL}`);
    console.log('');
    console.log('Block Range:');
    console.log(`  Start Height: ${CONFIG_SOLANA.START_HEIGHT} (Height ≈ Slot - 22M)`);
    console.log(`  End Height: ${CONFIG_SOLANA.END_HEIGHT || 'latest'}`);
    console.log(`  Batch Size: ${CONFIG_SOLANA.BATCH_SIZE}`);
    console.log('');
    console.log('Program IDs:');
    console.log(`  Jupiter V6: ${CONFIG_SOLANA.JUPITER_V6_PROGRAM_ID}`);
    console.log(`  Jupiter V4: ${CONFIG_SOLANA.JUPITER_V4_PROGRAM_ID}`);
    console.log(`  Pump.fun: ${CONFIG_SOLANA.PUMP_PROGRAM_ID}`);
    console.log('');
    console.log('Reference Tokens:');
    console.log(`  Native SOL: ${CONFIG_SOLANA.SOLANA_NATIVE_TOKEN_ADDRESS}`);
    console.log(`  USDC: ${CONFIG_SOLANA.SOLANA_USDC_ADDRESS}`);
    console.log('');
    console.log('Output:');
    console.log(`  Destination: ${CONFIG_SOLANA.OUTPUT}`);
    console.log(`  Entity Types: ${CONFIG_SOLANA.ENTITY_TYPES}`);
    console.log(`  Saving Entities: ${CONFIG_SOLANA.SAVING_ENTITIES}`);
    console.log('');
}

/**
 * ClickHouse configuration (for backwards compatibility with existing code)
 */
export const CLICKHOUSE_CONFIG = {
    url: CONFIG_SOLANA.CLICKHOUSE_HOST,
    username: CONFIG_SOLANA.CLICKHOUSE_USER,
    password: CONFIG_SOLANA.CLICKHOUSE_PASSWORD,
    database: CONFIG_SOLANA.CLICKHOUSE_DATABASE,
} as const;

/**
 * General config (for backwards compatibility)
 */
export const CONFIG = {
    CLICKHOUSE_TIMEOUT: parseInt(process.env.CLICKHOUSE_TIMEOUT || '30000'),
    CLICKHOUSE_MAX_RETRIES: parseInt(process.env.CLICKHOUSE_MAX_RETRIES || '3'),
    CLICKHOUSE_RETRY_DELAY: parseInt(process.env.CLICKHOUSE_RETRY_DELAY || '1000'),
    CLICKHOUSE_MAX_RETRY_DELAY: parseInt(process.env.CLICKHOUSE_MAX_RETRY_DELAY || '10000'),
} as const;

