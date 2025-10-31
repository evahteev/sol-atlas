// Solana-specific constants for the indexer

// Program IDs (Base58)
export const JUPITER_V6_PROGRAM_ID = 'JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4';
export const JUPITER_V4_PROGRAM_ID = 'JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB';
export const PUMP_PROGRAM_ID = '6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P';

// Native token (wrapped SOL)
export const NATIVE_SOL_ADDRESS = 'So11111111111111111111111111111111111111112';

// USDC on Solana
export const SOLANA_USDC_ADDRESS = 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v';

/**
 * Discriminators for event identification
 * 
 * These are the first 8-16 bytes of instruction data that identify the event type.
 * They are derived from the event name hash in the Solana program.
 * 
 * Source: workdir/donor_repo/decoders/
 */

// Jupiter V6 SwapEvent discriminator (16 bytes)
// From: carbon/decoders/jupiter-swap-decoder/src/instructions/swap_event.rs
// CRITICAL: Must use full 16 bytes to distinguish from FeeEvent and SwapsEvent which share first 8 bytes!
export const JUPITER_SWAP_EVENT_DISCRIMINATOR = Buffer.from([
    0xe4, 0x45, 0xa5, 0x2e, 0x51, 0xcb, 0x9a, 0x1d,
    0x40, 0xc6, 0xcd, 0xe8, 0x26, 0x08, 0x71, 0xe2,
]);

// Pump.fun TradeEvent discriminator (16 bytes)
// From: carbon/decoders/pumpfun-decoder/src/instructions/trade_event.rs
export const PUMP_TRADE_EVENT_DISCRIMINATOR = Buffer.from([
    0xe4, 0x45, 0xa5, 0x2e, 0x51, 0xcb, 0x9a, 0x1d,
    0xbd, 0xdb, 0x7f, 0xd3, 0x4e, 0xe6, 0x61, 0xee,
]);

/**
 * Helper function to check if instruction data matches a discriminator
 */
export function matchesDiscriminator(data: Buffer, discriminator: Buffer): boolean {
    if (data.length < discriminator.length) {
        return false;
    }
    
    for (let i = 0; i < discriminator.length; i++) {
        if (data[i] !== discriminator[i]) {
            return false;
        }
    }
    
    return true;
}

/**
 * Solana decimals (lamports)
 */
export const SOLANA_DECIMALS = 9;

/**
 * Account indices for Pump.fun instructions
 * Based on: carbon/decoders/pumpfun-decoder/src/instructions/
 */
export const PUMP_ACCOUNT_INDICES = {
    GLOBAL: 0,
    FEE_RECIPIENT: 1,
    MINT: 2,
    BONDING_CURVE: 3,
    ASSOCIATED_BONDING_CURVE: 4,
    ASSOCIATED_USER: 5,
    USER: 6,
} as const;


