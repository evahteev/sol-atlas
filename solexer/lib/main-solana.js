"use strict";
/**
 * Solana Indexer Main Processor
 *
 * This is the main entry point for the Solana indexer.
 * It processes Solana transactions and extracts DEX trades from Jupiter and Pump.fun.
 *
 * Uses @subsquid/solana-stream for proper Solana data access
 * Based on: https://github.com/subsquid/squid-sdk/tree/master/test/solana-example
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.main = main;
const solana_objects_1 = require("@subsquid/solana-objects");
const solana_stream_1 = require("@subsquid/solana-stream");
const web3_js_1 = require("@solana/web3.js");
const client_1 = require("@clickhouse/client");
const healthCheck_1 = require("./clickhouseClient/healthCheck");
const config_solana_1 = require("./config-solana");
const jupiter_parser_1 = require("./parsers/solana/jupiter-parser");
const pump_parser_1 = require("./parsers/solana/pump-parser");
const constants_solana_1 = require("./constants-solana");
const whitelist_1 = require("./utils/whitelist");
const state_manager_1 = require("./state-manager");
/**
 * Convert Subsquid instruction to our CompiledInstruction format
 */
function convertInstruction(ins, accountKeys) {
    // Find the program ID index in accountKeys
    const programIdIndex = accountKeys.findIndex(key => key.toBase58() === ins.programId);
    return {
        programIdIndex: programIdIndex >= 0 ? programIdIndex : 0,
        accounts: ins.accounts || [],
        data: ins.data || '',
    };
}
/**
 * Main processing function
 */
async function main() {
    console.log('🟣 Starting Solana Indexer (Subsquid)...');
    console.log('📚 Using @subsquid/solana-stream');
    console.log('');
    // Add global error handlers
    process.on('unhandledRejection', (reason, promise) => {
        console.error('❌ Unhandled Rejection at:', promise);
        console.error('❌ Reason:', reason);
        process.exit(1);
    });
    process.on('uncaughtException', (error) => {
        console.error('❌ Uncaught Exception:', error);
        process.exit(1);
    });
    // Perform health checks
    try {
        await (0, healthCheck_1.waitForClickHouse)();
        console.log('✅ ClickHouse connection verified');
    }
    catch (error) {
        console.error('❌ Health checks failed:', error);
        process.exit(1);
    }
    // Load whitelist
    (0, whitelist_1.loadWhitelist)();
    // Log configuration
    (0, config_solana_1.logSolanaConfiguration)();
    // Initialize ClickHouse client
    const database = config_solana_1.CONFIG_SOLANA.CLICKHOUSE_DATABASE || 'solana_indexer';
    const chClient = (0, client_1.createClient)({
        url: config_solana_1.CONFIG_SOLANA.CLICKHOUSE_HOST || 'http://localhost:8123',
        username: config_solana_1.CONFIG_SOLANA.CLICKHOUSE_USER || 'default',
        password: config_solana_1.CONFIG_SOLANA.CLICKHOUSE_PASSWORD || 'PASS',
        database: database,
    });
    console.log(`📊 Using ClickHouse database: ${database}`);
    console.log('');
    // Initialize state management
    await (0, state_manager_1.initializeStateManagement)(chClient, database);
    // Get starting block from state or config
    const startHeight = await (0, state_manager_1.getStartingBlock)(chClient, database, config_solana_1.CONFIG_SOLANA.CHAIN_ID);
    console.log(`📍 Starting from block HEIGHT: ${startHeight}`);
    console.log('⚠️  NOTE: Subsquid uses BLOCK HEIGHT, not SLOT! Height ≈ Slot - 22M');
    console.log('');
    // Program IDs to filter
    const programIds = [constants_solana_1.JUPITER_V6_PROGRAM_ID, constants_solana_1.JUPITER_V4_PROGRAM_ID, constants_solana_1.PUMP_PROGRAM_ID];
    // Create data source using Subsquid's DataSourceBuilder
    const dataSource = new solana_stream_1.DataSourceBuilder()
        // Use Subsquid Network Gateway
        .setGateway(config_solana_1.CONFIG_SOLANA.GATEWAY_URL || 'https://v2.archive.subsquid.io/network/solana-mainnet')
        // DISABLED: RPC endpoint causes consistency check errors with field names
        // The Gateway has enough historical data, we can enable this later for real-time
        // .setRpc(CONFIG_SOLANA.RPC_ENDPOINT ? {
        //     client: new SolanaRpcClient({
        //         url: CONFIG_SOLANA.RPC_ENDPOINT,
        //         // rateLimit: 100 // requests per sec
        //     }),
        //     strideConcurrency: 10
        // } : undefined)
        // Set block range
        // IMPORTANT: .setBlockRange() expects BLOCK HEIGHT, not SLOT!
        // As per subsquid-solana-example comment:
        // "NOTE, that block ranges are specified in heights, not in slots !!!"
        .setBlockRange({ from: startHeight })
        // Configure fields to fetch
        // Note: Don't explicitly request 'number' field - it's included by default
        // Requesting it explicitly causes the Gateway to try to use 'slot' internally
        .setFields({
        block: {
            timestamp: true,
        },
        transaction: {
            signatures: true,
            err: true,
            fee: true,
        },
        instruction: {
            programId: true,
            data: true,
            accounts: true,
            isCommitted: true,
        },
        tokenBalance: {
            preAmount: true,
            postAmount: true,
            preOwner: true,
            postOwner: true,
        },
        log: {
            programId: true,
            kind: true,
            message: true,
        }
    })
        // Add instruction filter with includes
        // This is the KEY part - we request instructions by programId
        // and use 'include' to get the parent transaction
        .addInstruction({
        where: {
            programId: programIds,
            isCommitted: true, // Only committed instructions
        },
        include: {
            innerInstructions: true,
            transaction: true, // <-- This ensures we get the parent transaction!
            transactionTokenBalances: true, // We NEED token balances for reliable parsing!
        }
    })
        .build();
    console.log('🚀 Starting block stream...');
    console.log('');
    // Performance tracking
    const indexerStartTime = Date.now();
    const indexerStartHeight = startHeight;
    let totalBlocksProcessed = 0;
    let batchCount = 0;
    let currentChainHeight = null;
    let slotToHeightOffset = null; // Dynamic offset calculated from actual data
    // Function to get current chain height from RPC
    async function getCurrentChainHeight(calculatedOffset) {
        try {
            const { Connection } = await Promise.resolve().then(() => __importStar(require('@solana/web3.js')));
            const connection = new Connection(config_solana_1.CONFIG_SOLANA.RPC_URL);
            const currentSlot = await connection.getSlot();
            // Use calculated offset from actual block data if available
            const offset = calculatedOffset || 22000000;
            const height = currentSlot - offset;
            return height;
        }
        catch (error) {
            console.warn(`   ⚠️  Could not fetch current chain height: ${error.message}`);
            return null;
        }
    }
    // Function to format duration
    function formatDuration(ms) {
        const seconds = Math.floor(ms / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        const days = Math.floor(hours / 24);
        if (days > 0)
            return `${days}d ${hours % 24}h ${minutes % 60}m`;
        if (hours > 0)
            return `${hours}h ${minutes % 60}m ${seconds % 60}s`;
        if (minutes > 0)
            return `${minutes}m ${seconds % 60}s`;
        return `${seconds}s`;
    }
    // Get current chain height at start (with approximate offset)
    console.log('📡 Fetching current chain height...');
    console.log('   (Will recalculate with accurate offset after first batch)');
    console.log('');
    // Iterate through blocks directly (simpler than using run() with TypeORM)
    try {
        for await (let batch of dataSource.getBlockStream()) {
            // Augment blocks with convenient getters and references
            const blocks = batch.map(solana_objects_1.augmentBlock);
            // Update counters
            totalBlocksProcessed += blocks.length;
            batchCount++;
            // Calculate accurate slot-to-height offset from first batch
            if (!slotToHeightOffset && blocks.length > 0) {
                const firstBlock = blocks[0];
                const blockHeight = firstBlock.header.height;
                const blockSlot = firstBlock.header.slot;
                slotToHeightOffset = blockSlot - blockHeight;
                console.log(`📐 Calculated slot-to-height offset: ${slotToHeightOffset.toLocaleString()}`);
                console.log(`   (Slot ${blockSlot.toLocaleString()} - Height ${blockHeight.toLocaleString()})`);
                // Now get accurate current chain height
                currentChainHeight = await getCurrentChainHeight(slotToHeightOffset);
                if (currentChainHeight) {
                    console.log(`📡 Current chain height: ~${currentChainHeight.toLocaleString()}`);
                    const blocksToSync = currentChainHeight - blockHeight;
                    console.log(`   Blocks to sync: ~${blocksToSync.toLocaleString()}`);
                }
                console.log('');
            }
            let jupiterCount = 0;
            let pumpCount = 0;
            const allTrades = [];
            for (const block of blocks) {
                for (const ins of block.instructions) {
                    try {
                        // Get the parent transaction
                        const transaction = ins.getTransaction();
                        if (!transaction) {
                            continue;
                        }
                        // Skip failed transactions
                        if (transaction.err) {
                            continue;
                        }
                        // Get account keys - these are available on the transaction
                        const accountKeys = [];
                        // Extract account keys from the instruction and transaction
                        // Subsquid provides them differently than standard RPC
                        for (const account of ins.accounts || []) {
                            try {
                                if (typeof account === 'string') {
                                    accountKeys.push(new web3_js_1.PublicKey(account));
                                }
                                else if (account && typeof account === 'object' && 'toBase58' in account) {
                                    // Already a PublicKey-like object
                                    accountKeys.push(account);
                                }
                            }
                            catch (e) {
                                // Invalid public key, skip
                            }
                        }
                        // Add program ID to account keys if not already there
                        try {
                            const programId = new web3_js_1.PublicKey(ins.programId);
                            if (!accountKeys.some(k => k.equals(programId))) {
                                accountKeys.push(programId);
                            }
                        }
                        catch (e) {
                            // Invalid program ID
                        }
                        // Convert inner instructions
                        // Subsquid provides ins.inner as flat array of all inner instructions
                        // We need to structure it as: [{ index: topLevelIndex, instructions: [...] }]
                        const innerInstructionsConverted = (ins.inner || []).map((innerIns) => {
                            return convertInstruction(innerIns, accountKeys);
                        });
                        // Group all inner instructions under index 0 (for parsers)
                        const innerInstructions = innerInstructionsConverted.length > 0 ? [{
                                index: 0, // Parsers look for innerInstructions with index matching instruction
                                instructions: innerInstructionsConverted
                            }] : [];
                        // Get log messages for this transaction
                        const logMessages = block.logs
                            .filter((log) => {
                            // Match logs to this transaction
                            // Subsquid may provide a transaction reference or we compare by other means
                            return true; // For now, include all logs from the block
                        })
                            .map((log) => log.message || '');
                        // Extract token balances from transaction
                        // Subsquid provides tokenBalances on the transaction
                        // See subsquid-solana-example for field structure
                        const tokenBalances = transaction.tokenBalances || [];
                        const preTokenBalances = tokenBalances.map((tb) => ({
                            accountIndex: 0,
                            mint: tb.preMint || '',
                            owner: tb.preOwner || '',
                            uiTokenAmount: {
                                amount: tb.preAmount || '0',
                                decimals: 0, // Not provided by Subsquid
                                uiAmount: null,
                                uiAmountString: tb.preAmount || '0',
                            },
                        }));
                        const postTokenBalances = tokenBalances.map((tb) => ({
                            accountIndex: 0,
                            mint: tb.postMint || tb.preMint || '',
                            owner: tb.postOwner || '',
                            uiTokenAmount: {
                                amount: tb.postAmount || '0',
                                decimals: 0, // Not provided by Subsquid
                                uiAmount: null,
                                uiAmountString: tb.postAmount || '0',
                            },
                        }));
                        // Build transaction object for parsers
                        const solanaTransaction = {
                            signature: transaction.signatures[0],
                            slot: block.header.slot, // After augmentBlock(), 'number' field becomes 'slot'
                            blockTime: block.header.timestamp,
                            meta: {
                                err: transaction.err || null,
                                fee: Number(transaction.fee || 0),
                                innerInstructions: innerInstructions,
                                preBalances: [],
                                postBalances: [],
                                preTokenBalances: preTokenBalances,
                                postTokenBalances: postTokenBalances,
                                logMessages: logMessages,
                            },
                            transaction: {
                                message: {
                                    accountKeys: accountKeys,
                                    instructions: [convertInstruction(ins, accountKeys)],
                                },
                                signatures: transaction.signatures,
                            },
                        };
                        // Parse based on program ID
                        if (ins.programId === constants_solana_1.JUPITER_V6_PROGRAM_ID || ins.programId === constants_solana_1.JUPITER_V4_PROGRAM_ID) {
                            const jupiterTrades = await (0, jupiter_parser_1.parseJupiterTransaction)(solanaTransaction);
                            if (jupiterTrades.length > 0) {
                                jupiterCount += jupiterTrades.length;
                                allTrades.push(...jupiterTrades);
                            }
                        }
                        else if (ins.programId === constants_solana_1.PUMP_PROGRAM_ID) {
                            const pumpTrades = await (0, pump_parser_1.parsePumpTransaction)(solanaTransaction);
                            if (pumpTrades.length > 0) {
                                pumpCount += pumpTrades.length;
                                allTrades.push(...pumpTrades);
                            }
                        }
                    }
                    catch (error) {
                        console.error(`   ❌ Error parsing instruction:`, error.message);
                    }
                }
            }
            // Log batch summary
            const totalInstructions = blocks.reduce((sum, b) => sum + b.instructions.length, 0);
            const heightRange = blocks.length > 0
                ? `${blocks[0].header.height} - ${blocks[blocks.length - 1].header.height}`
                : 'no blocks';
            const slotRange = blocks.length > 0
                ? `${blocks[0].header.slot} - ${blocks[blocks.length - 1].header.slot}`
                : 'no blocks';
            console.log(`\n📦 Batch processed: ${blocks.length} blocks`);
            console.log(`   Heights: ${heightRange} | Slots: ${slotRange}`);
            console.log(`   Instructions: ${totalInstructions} total`);
            console.log(`   Trades found: ${allTrades.length} (Jupiter: ${jupiterCount}, Pump: ${pumpCount})`);
            // Performance metrics
            const elapsedMs = Date.now() - indexerStartTime;
            const elapsedSeconds = elapsedMs / 1000;
            const blocksPerSecond = elapsedSeconds > 0 ? totalBlocksProcessed / elapsedSeconds : 0;
            console.log(`\n⚡ Performance:`);
            console.log(`   Batches processed: ${batchCount} (${blocks.length} blocks in current batch, ${totalBlocksProcessed.toLocaleString()} total)`);
            console.log(`   Speed: ${blocksPerSecond.toFixed(2)} blocks/sec (overall since start)`);
            console.log(`   Running time: ${formatDuration(elapsedMs)}`);
            // Calculate ETA and progress
            if (blocks.length > 0) {
                const currentHeight = blocks[blocks.length - 1].header.height;
                // Try to use fetched chain height, or estimate if not available
                const targetHeight = currentChainHeight || (config_solana_1.CONFIG_SOLANA.END_HEIGHT || currentHeight + 1000000);
                const remainingBlocks = targetHeight - currentHeight;
                if (remainingBlocks > 0 && blocksPerSecond > 0) {
                    const etaSeconds = remainingBlocks / blocksPerSecond;
                    const etaMs = etaSeconds * 1000;
                    const progress = ((currentHeight - indexerStartHeight) / (targetHeight - indexerStartHeight)) * 100;
                    console.log(`   Progress: ${progress.toFixed(2)}% (${remainingBlocks.toLocaleString()} blocks remaining)`);
                    console.log(`   ETA to sync: ${formatDuration(etaMs)}${!currentChainHeight ? ' (estimated)' : ''}`);
                }
                else if (remainingBlocks <= 0) {
                    console.log(`   Progress: 100.00% (0 blocks remaining)`);
                    console.log(`   ETA to sync: 0s - ✅ Synced at chain tip!`);
                }
                else {
                    console.log(`   Current height: ${currentHeight.toLocaleString()}`);
                    console.log(`   ETA to sync: Calculating...`);
                }
            }
            // Save to ClickHouse and update state
            if (allTrades.length > 0) {
                try {
                    await chClient.insert({
                        table: `${database}.dex_trades`,
                        values: allTrades.map((trade) => ({
                            block_number: trade.block_number,
                            block_hash: trade.block_hash || '',
                            block_timestamp: trade.block_timestamp,
                            transaction_hash: trade.transaction_hash,
                            log_index: trade.log_index,
                            transaction_type: trade.event_type,
                            swap_type: trade.swap_type || 'buy',
                            token_addresses: trade.token_addresses,
                            amounts: trade.token_amounts.map(a => parseFloat(a) || 0),
                            amount_stable: parseFloat(trade.amount_stable || '0'),
                            amount_native: parseFloat(trade.amount_native || '0'),
                            prices_stable: (trade.prices_stable || []).map(p => parseFloat(p) || 0),
                            prices_native: (trade.prices_native || []).map(p => parseFloat(p) || 0),
                            pool_address: trade.pool_address,
                            factory_address: trade.factory_address || '',
                            lp_token_address: trade.lp_token_address || '',
                            reserves: (trade.reserves || trade.token_reserves || []).map(r => parseFloat(r) || 0),
                            reserves_stable: (trade.reserves_stable || []).map(r => parseFloat(r) || 0),
                            reserves_native: (trade.reserves_native || []).map(r => parseFloat(r) || 0),
                            wallet_address: trade.wallet_address,
                            is_reorged: trade.is_reorged || 0,
                        })),
                        format: 'JSONEachRow',
                    });
                    console.log(`   💾 Saved to ClickHouse`);
                }
                catch (error) {
                    console.error(`   ❌ ClickHouse error:`, error.message);
                }
            }
            // Update state with the latest HEIGHT from this batch
            // IMPORTANT: We save HEIGHT (not slot) because Subsquid uses heights for block ranges
            if (blocks.length > 0) {
                try {
                    const lastBlock = blocks[blocks.length - 1];
                    const latestHeight = lastBlock.header.height;
                    const latestSlot = lastBlock.header.slot;
                    await (0, state_manager_1.updateLastProcessedBlock)(chClient, database, latestHeight, config_solana_1.CONFIG_SOLANA.CHAIN_ID);
                    console.log(`   📌 State saved: height ${latestHeight} (slot ${latestSlot})`);
                }
                catch (error) {
                    console.error(`   ⚠️  Failed to update state:`, error.message);
                }
            }
        }
        console.log('✅ Indexer finished successfully');
    }
    catch (error) {
        console.error('❌ Fatal error in main loop:', error);
        if (error instanceof Error) {
            console.error('Stack trace:', error.stack);
        }
        throw error;
    }
}
/**
 * Graceful shutdown handlers
 */
process.on('SIGINT', async () => {
    console.log('⚠️  SIGINT received, shutting down gracefully...');
    process.exit(0);
});
process.on('SIGTERM', async () => {
    console.log('⚠️  SIGTERM received, shutting down gracefully...');
    process.exit(0);
});
// Run main with error handling
main().catch((error) => {
    console.error('❌ Fatal error in main():', error);
    if (error instanceof Error) {
        console.error('Stack trace:', error.stack);
    }
    process.exit(1);
});
