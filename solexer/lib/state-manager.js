"use strict";
/**
 * State Manager for Solana Indexer
 *
 * Manages persistent state in ClickHouse to track indexing progress.
 * This allows the indexer to resume from where it left off instead of
 * relying solely on environment variables.
 *
 * IMPORTANT: Subsquid uses BLOCK HEIGHT, not SLOT!
 * - Solana Slot: The actual on-chain slot number
 * - Subsquid Height: Block height ≈ Slot - 22M (approximate, not exact)
 *
 * We store HEIGHTS in the database to avoid confusion and make it consistent
 * with what Subsquid expects.
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.slotToHeight = slotToHeight;
exports.heightToSlot = heightToSlot;
exports.getLastProcessedBlock = getLastProcessedBlock;
exports.updateLastProcessedBlock = updateLastProcessedBlock;
exports.getStartingBlock = getStartingBlock;
exports.initializeStateManagement = initializeStateManagement;
const config_solana_1 = require("./config-solana");
/**
 * Convert Solana slot to Subsquid block height
 *
 * NOTE: This is an approximation. The exact offset varies slightly.
 * Subsquid's height is derived from actual blocks, not a fixed offset.
 * Use the height provided directly by Subsquid when available.
 *
 * @param slot - Solana slot number
 * @returns Approximate block height
 */
function slotToHeight(slot) {
    // Approximate conversion: height ≈ slot - 22M
    // This is just for initial conversion from config
    const APPROXIMATE_OFFSET = 22000000;
    return slot - APPROXIMATE_OFFSET;
}
/**
 * Convert Subsquid block height to approximate Solana slot
 *
 * @param height - Subsquid block height
 * @returns Approximate Solana slot number
 */
function heightToSlot(height) {
    const APPROXIMATE_OFFSET = 22000000;
    return height + APPROXIMATE_OFFSET;
}
/**
 * Get the latest processed block from the database
 *
 * @param client - ClickHouse client
 * @param database - Database name
 * @param chain - Chain identifier (default: solana-mainnet)
 * @returns The last processed block HEIGHT, or null if no state exists
 */
async function getLastProcessedBlock(client, database, chain = 'solana-mainnet') {
    try {
        // Query the state table with FINAL to get the latest version
        // ReplacingMergeTree uses the version column to determine the latest value
        const result = await client.query({
            query: `
                SELECT state_value 
                FROM ${database}.solana_indexer_state FINAL
                WHERE chain = {chain:String} 
                  AND state_key = 'last_processed_block'
                ORDER BY version DESC
                LIMIT 1
            `,
            query_params: {
                chain: chain,
            },
            format: 'JSONEachRow',
        });
        const data = await result.json();
        if (data.length > 0 && data[0].state_value) {
            let value = parseInt(data[0].state_value, 10);
            if (!isNaN(value)) {
                // MIGRATION FIX: Detect if the stored value is actually a SLOT (not height)
                // Heights are typically < 360M, slots are typically > 370M
                // If value is too high, it's probably a slot that was incorrectly saved
                if (value > 365000000) {
                    console.log(`   ⚠️  Detected SLOT in state (${value}), converting to HEIGHT...`);
                    value = slotToHeight(value);
                    console.log(`   ✅ Converted to HEIGHT: ${value}`);
                }
                return value;
            }
        }
        return null;
    }
    catch (error) {
        // If table doesn't exist yet, return null
        if (error.message && error.message.includes('doesn\'t exist')) {
            console.log('   ℹ️  State table does not exist yet, will use START_HEIGHT from config');
            return null;
        }
        console.error('   ⚠️  Error reading state from database:', error.message);
        return null;
    }
}
/**
 * Update the latest processed block in the database
 *
 * IMPORTANT: Save the HEIGHT (from Subsquid), not the slot!
 *
 * @param client - ClickHouse client
 * @param database - Database name
 * @param height - The block HEIGHT to save (NOT slot!)
 * @param chain - Chain identifier (default: solana-mainnet)
 */
async function updateLastProcessedBlock(client, database, height, chain = 'solana-mainnet') {
    try {
        // Validation: height should be reasonable (not a slot)
        if (height > 365000000) {
            console.warn(`   ⚠️  WARNING: Trying to save height ${height} which looks like a SLOT!`);
            console.warn(`   ⚠️  Heights should be < 365M. Slots are ~22M higher.`);
        }
        // Insert with incrementing version for ReplacingMergeTree
        // The version ensures the latest update wins
        await client.insert({
            table: `${database}.solana_indexer_state`,
            values: [{
                    state_key: 'last_processed_block',
                    state_value: height.toString(),
                    chain: chain,
                    updated_at: Math.floor(Date.now() / 1000), // Unix timestamp in seconds
                    version: Date.now(), // Use milliseconds timestamp as version for uniqueness
                }],
            format: 'JSONEachRow',
        });
    }
    catch (error) {
        console.error('   ⚠️  Error updating state in database:', error.message);
        throw error;
    }
}
/**
 * Get the starting block for the indexer
 *
 * Priority:
 * 1. Last processed block from database (if exists)
 * 2. START_HEIGHT from environment variables
 *
 * @param client - ClickHouse client
 * @param database - Database name
 * @param chain - Chain identifier (default: solana-mainnet)
 * @returns The block number to start indexing from
 */
async function getStartingBlock(client, database, chain = 'solana-mainnet') {
    // Try to get last processed block from database
    const lastProcessedBlock = await getLastProcessedBlock(client, database, chain);
    if (lastProcessedBlock !== null) {
        console.log(`✅ Resuming from last processed block: ${lastProcessedBlock}`);
        console.log(`   (State loaded from database)`);
        // Start from the next block after the last processed one
        return lastProcessedBlock + 1;
    }
    // Fall back to environment variable
    const startHeight = config_solana_1.CONFIG_SOLANA.START_HEIGHT;
    console.log(`✅ Starting from configured block: ${startHeight}`);
    console.log(`   (No state found in database, using START_HEIGHT from config)`);
    return startHeight;
}
/**
 * Initialize state management system
 * Ensures the state table exists
 *
 * @param client - ClickHouse client
 * @param database - Database name
 */
async function initializeStateManagement(client, database) {
    console.log('🔧 Initializing state management...');
    try {
        // Check if state table exists
        const result = await client.query({
            query: `
                SELECT count() as count
                FROM system.tables
                WHERE database = {database:String}
                  AND name = 'solana_indexer_state'
            `,
            query_params: {
                database: database,
            },
            format: 'JSONEachRow',
        });
        const data = await result.json();
        if (data.length > 0 && parseInt(data[0].count) > 0) {
            console.log('✅ State table exists');
        }
        else {
            console.log('⚠️  State table does not exist. Please run migrations:');
            console.log('   cd db && alembic upgrade head');
        }
    }
    catch (error) {
        console.error('⚠️  Error checking state table:', error.message);
    }
}
