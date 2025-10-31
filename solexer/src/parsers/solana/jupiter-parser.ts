/**
 * Jupiter Transaction Parser
 * 
 * Parses Jupiter V6 swap transactions and converts them to DexTrade format.
 * Based on: workdir/donor_repo/examples/jupiter-swap-alerts/
 * 
 * METHODOLOGY (from donor repo):
 * 1. Jupiter Route/SharedAccountsRoute instructions trigger swaps at top level
 * 2. Jupiter program emits SwapEvent as an INNER INSTRUCTION for each swap leg
 * 3. SwapEvent has 16-byte discriminator: 0xe445a52e51cb9a1d40c6cde8260871e2
 * 4. CRITICAL: Must check FULL 16 bytes - FeeEvent (0xe445a52e51cb9a1d494f4e7fb8d50ddc) 
 *    and SwapsEvent (0xe445a52e51cb9a1d982f4eebc0606e6a) share first 8 bytes!
 * 5. SwapEvent contains: amm, inputMint, inputAmount, outputMint, outputAmount
 * 6. Each inner instruction from Jupiter program could be a SwapEvent
 */

import { SolanaTransaction, CompiledInstruction } from '../../types-solana';
import { DexTrade } from '../../types';
import bs58 from 'bs58';
import { deserializeJupiterSwapEvent } from './jupiter-deserializer';
import { JUPITER_V6_PROGRAM_ID, JUPITER_V4_PROGRAM_ID, NATIVE_SOL_ADDRESS, SOLANA_USDC_ADDRESS } from '../../constants-solana';
import { hasWhitelistedToken } from '../../utils/whitelist';

/**
 * Parse Jupiter transactions and extract swap events
 * 
 * Following Carbon framework methodology:
 * - Process top-level instructions that call Jupiter
 * - For each Jupiter instruction, recursively check inner instructions
 * - SwapEvent is emitted as inner instruction with specific discriminator
 * 
 * @param tx - Solana transaction
 * @returns Array of parsed DexTrade objects
 */
export async function parseJupiterTransaction(
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
        
        // Check if this is a Jupiter instruction
        if (programId !== JUPITER_V6_PROGRAM_ID && programId !== JUPITER_V4_PROGRAM_ID) {
            continue;
        }
        
        // Get inner instructions for this top-level instruction
        const innerInstructions = tx.meta.innerInstructions?.find(
            inner => inner.index === i
        );
        
        if (!innerInstructions) {
            continue;
        }
        
        // Process inner instructions for SwapEvent
        // Jupiter emits SwapEvent as inner instructions (NOT in logs like Anchor typically does)
        for (const innerIx of innerInstructions.instructions) {
            const innerProgramId = message.accountKeys[innerIx.programIdIndex]?.toBase58();
            
            // Check if this inner instruction is from Jupiter program
            // SwapEvent will have programId = Jupiter program
            if (innerProgramId === JUPITER_V6_PROGRAM_ID || innerProgramId === JUPITER_V4_PROGRAM_ID) {
                try {
                    // Decode base58 instruction data
                    const data = bs58.decode(innerIx.data);
                    
                    // Try to deserialize as SwapEvent
                    // This checks the 16-byte discriminator and Borsh structure
                    const swapEvent = deserializeJupiterSwapEvent(Buffer.from(data));
                    
                    if (swapEvent) {
                        const trade = convertJupiterEventToTrade(swapEvent, tx, i);
                        
                        // Apply whitelist filter: only save trades involving whitelisted tokens
                        if (hasWhitelistedToken(trade.token_addresses)) {
                            trades.push(trade);
                        }
                    }
                    // If not a SwapEvent, it might be FeeEvent, SwapsEvent, or other Jupiter inner instruction
                } catch (error) {
                    // Deserialization failed - not a valid SwapEvent
                    // This is expected for other Jupiter instructions
                }
            }
        }
    }
    
    return trades;
}

/**
 * Convert Jupiter SwapEvent to DexTrade format
 */
function convertJupiterEventToTrade(
    event: any,
    tx: SolanaTransaction,
    topLevelIndex: number
): DexTrade {
    // Calculate price
    const inAmount = Number(event.inputAmount);
    const outAmount = Number(event.outputAmount);
    const price = inAmount / outAmount;
    
    // Token IN is always at index 0, Token OUT at index 1 (follow event's natural order)
    const tokenIn = event.inputMint.toBase58();
    const tokenOut = event.outputMint.toBase58();
    
    // Determine swap_type: 'sell' only if token OUT is WSOL or USDC
    const swapType = (tokenOut === NATIVE_SOL_ADDRESS || tokenOut === SOLANA_USDC_ADDRESS) ? 'sell' : 'buy';
    
    // amount_native should always be the SOL amount
    const amount_native = (tokenIn === NATIVE_SOL_ADDRESS) 
        ? event.inputAmount.toString() 
        : (tokenOut === NATIVE_SOL_ADDRESS) 
            ? event.outputAmount.toString() 
            : '0';
    
    const trade: DexTrade = {
        transaction_hash: tx.signature,
        block_number: tx.slot,
        block_timestamp: tx.blockTime || 0,
        block_hash: '',
        
        pool_address: event.amm.toBase58(),
        wallet_address: tx.transaction.message.accountKeys[0]?.toBase58() || '',
        
        // Token IN (spent) is always at index 0, Token OUT (received) at index 1
        token_addresses: [tokenIn, tokenOut],
        token_amounts: [
            event.inputAmount.toString(),
            event.outputAmount.toString()
        ],
        
        event_type: 'swap',
        amm: 'jupiter_v6',
        swap_type: swapType,
        
        log_index: topLevelIndex,
        lp_token_address: '',
        factory_address: JUPITER_V6_PROGRAM_ID,
        
        token_reserves: [],
        token_prices: [[price.toString()]],
        
        amount_native: amount_native,
        prices_native: [price.toString()],
        
        is_reorged: 0,
    };
    
    return trade;
}


