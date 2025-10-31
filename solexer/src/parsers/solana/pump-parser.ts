/**
 * Pump.fun Transaction Parser
 * 
 * Parses Pump.fun trade transactions and converts them to DexTrade format.
 * Based on: workdir/donor_repo/examples/pumpfun-alerts/
 * 
 * METHODOLOGY (from donor repo):
 * 1. Pump Buy/Sell instructions trigger trades
 * 2. TradeEvent is emitted as an INNER INSTRUCTION (CPI event) by Pump program
 * 3. TradeEvent has discriminator: 0xe445a52e51cb9a1dbddb7fd34ee661ee
 * 4. We must recursively check ALL inner instructions for TradeEvent
 * 5. TradeEvent contains ALL trade data including user, amounts, and reserves
 */

import bs58 from 'bs58';
import { SolanaTransaction, CompiledInstruction } from '../../types-solana';
import { DexTrade } from '../../types';
import { deserializePumpTradeEvent } from './pump-deserializer';
import { PUMP_PROGRAM_ID, NATIVE_SOL_ADDRESS, PUMP_ACCOUNT_INDICES, SOLANA_USDC_ADDRESS } from '../../constants-solana';
import { hasWhitelistedToken } from '../../utils/whitelist';

/**
 * Parse Pump.fun transactions and extract trade events
 * 
 * Following Carbon framework methodology:
 * - Process top-level instructions that call Pump.fun
 * - For each Pump instruction, recursively check inner instructions
 * - TradeEvent is emitted as inner instruction with specific discriminator
 * 
 * @param tx - Solana transaction
 * @returns Array of parsed DexTrade objects
 */
export async function parsePumpTransaction(
    tx: SolanaTransaction
): Promise<DexTrade[]> {
    const trades: DexTrade[] = [];
    
    // Skip failed transactions
    if (!tx.meta || tx.meta.err) {
        return trades;
    }
    
    const message = tx.transaction.message;
    
    // Process top-level instructions
    for (let i = 0; i < message.instructions.length; i++) {
        const instruction = message.instructions[i];
        const programId = message.accountKeys[instruction.programIdIndex]?.toBase58();
        
        if (!programId) {
            continue;
        }
        
        // Check if this is a Pump.fun instruction
        if (programId !== PUMP_PROGRAM_ID) {
            continue;
        }
        
        // Get inner instructions for this top-level instruction
        const innerInstructions = tx.meta.innerInstructions?.find(
            inner => inner.index === i
        );
        
        if (!innerInstructions) {
            continue;
        }
        
        // Recursively parse ALL inner instructions for TradeEvent
        // This is critical - TradeEvent can be nested at any depth
        const events = await extractTradeEventsRecursively(
            innerInstructions.instructions,
            message.accountKeys,
            tx,
            i,
            instruction
        );
        
        trades.push(...events);
    }
    
    return trades;
}

/**
 * Recursively extract TradeEvents from inner instructions
 * 
 * Based on Carbon framework's recursive instruction processing
 * (see: workdir/donor_repo/crates/core/src/instruction.rs)
 * 
 * @param instructions - Inner instructions to process
 * @param accountKeys - Transaction account keys
 * @param tx - Parent transaction
 * @param topLevelIndex - Index of top-level instruction
 * @param parentInstruction - Parent instruction (for extracting bonding curve)
 * @returns Array of DexTrade objects
 */
async function extractTradeEventsRecursively(
    instructions: CompiledInstruction[],
    accountKeys: any[],
    tx: SolanaTransaction,
    topLevelIndex: number,
    parentInstruction: CompiledInstruction
): Promise<DexTrade[]> {
    const trades: DexTrade[] = [];
    
    for (const innerIx of instructions) {
        const innerProgramId = accountKeys[innerIx.programIdIndex]?.toBase58();
        
        // Check if this inner instruction is from Pump.fun program
        if (innerProgramId === PUMP_PROGRAM_ID) {
            try {
                // Decode base58 instruction data
                const data = bs58.decode(innerIx.data);
                const tradeEvent = deserializePumpTradeEvent(Buffer.from(data));
                
                if (tradeEvent) {
                    const trade = convertPumpEventToTrade(
                        tradeEvent,
                        tx,
                        topLevelIndex,
                        parentInstruction,
                        accountKeys
                    );
                    
                    // Apply whitelist filter: only save trades involving whitelisted tokens
                    if (hasWhitelistedToken(trade.token_addresses)) {
                        trades.push(trade);
                    }
                }
            } catch (error) {
                // Not a TradeEvent, continue
            }
        }
        
        // Note: Inner instructions don't have nested inner instructions in Solana's data structure
        // The recursion here is conceptual - all CPIs are flattened into innerInstructions array
    }
    
    return trades;
}

/**
 * Convert Pump TradeEvent to DexTrade format
 * 
 * @param event - Parsed TradeEvent
 * @param tx - Solana transaction
 * @param instructionIndex - Index of parent instruction
 * @param instruction - Parent instruction (to extract accounts)
 * @param accountKeys - Transaction account keys
 * @returns DexTrade object
 */
function convertPumpEventToTrade(
    event: any,
    tx: SolanaTransaction,
    instructionIndex: number,
    instruction: CompiledInstruction,
    accountKeys: any[]
): DexTrade {
    // Extract bonding curve address from instruction accounts
    // Account[3] is the bonding_curve account (based on Pump.fun program)
    let bondingCurveAddress = '';
    try {
        if (instruction.accounts && instruction.accounts.length > PUMP_ACCOUNT_INDICES.BONDING_CURVE) {
            const accountIndex = instruction.accounts[PUMP_ACCOUNT_INDICES.BONDING_CURVE];
            bondingCurveAddress = accountKeys[accountIndex]?.toBase58() || '';
        }
    } catch (error) {
        // Fallback to mint address
        bondingCurveAddress = event.mint.toBase58();
    }
    
    // Calculate price (SOL amount / token amount)
    const price = calculatePrice(event.solAmount, event.tokenAmount);
    
    // CRITICAL: Token IN must always be at index 0, Token OUT at index 1
    // Follow the event's natural flow:
    // - isBuy=true: User spends SOL (IN) to get tokens (OUT) -> [SOL, token]
    // - isBuy=false: User spends tokens (IN) to get SOL (OUT) -> [token, SOL]
    const tokenAddresses = event.isBuy
        ? [NATIVE_SOL_ADDRESS, event.mint.toBase58()]
        : [event.mint.toBase58(), NATIVE_SOL_ADDRESS];
    
    const tokenAmounts = event.isBuy
        ? [event.solAmount.toString(), event.tokenAmount.toString()]
        : [event.tokenAmount.toString(), event.solAmount.toString()];
    
    const tokenReserves = event.isBuy
        ? [event.realSolReserves.toString(), event.realTokenReserves.toString()]
        : [event.realTokenReserves.toString(), event.realSolReserves.toString()];
    
    // Determine swap_type: 'sell' only if token OUT is WSOL or USDC
    const tokenOut = tokenAddresses[1];
    const swapType = (tokenOut === NATIVE_SOL_ADDRESS || tokenOut === SOLANA_USDC_ADDRESS) ? 'sell' : 'buy';
    
    const trade: DexTrade = {
        // Transaction metadata
        transaction_hash: tx.signature,
        block_number: tx.slot,
        block_timestamp: Number(event.timestamp), // Pump events include timestamp
        block_hash: '',
        
        // Pool and wallet (Pump event includes wallet address!)
        pool_address: bondingCurveAddress,
        wallet_address: event.user.toBase58(),
        
        // Token information
        // Token IN (spent) is always at index 0, Token OUT (received) at index 1
        token_addresses: tokenAddresses,
        token_amounts: tokenAmounts,
        
        // Reserves (available in Pump TradeEvent!)
        token_reserves: tokenReserves,
        
        // Event details
        event_type: 'swap',
        amm: 'pump',
        swap_type: swapType,
        
        // Additional fields
        log_index: instructionIndex,
        lp_token_address: '',
        factory_address: PUMP_PROGRAM_ID,
        
        // Prices
        token_prices: [[price]],
        amount_native: event.solAmount.toString(),
        prices_native: [price],
        
        // Reserves in native terms
        reserves_native: [event.realSolReserves.toString()],
        
        // Status
        is_reorged: 0,
    };
    
    return trade;
}

/**
 * Calculate price from SOL and token amounts
 * 
 * @param solAmount - SOL amount
 * @param tokenAmount - Token amount
 * @returns Price as string (SOL per token)
 */
function calculatePrice(solAmount: bigint, tokenAmount: bigint): string {
    if (tokenAmount === 0n) {
        return '0';
    }
    
    // Convert to number for division (acceptable for price calculation)
    const price = Number(solAmount) / Number(tokenAmount);
    return price.toString();
}


