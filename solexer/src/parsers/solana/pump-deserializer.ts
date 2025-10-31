/**
 * Pump.fun TradeEvent Deserializer
 * 
 * Deserializes Pump.fun TradeEvent from instruction data using Borsh.
 * Based on: workdir/donor_repo/decoders/pumpfun-decoder/
 */

import { struct, u64, i64, bool, publicKey } from '@coral-xyz/borsh';
import { PublicKey } from '@solana/web3.js';
import { PumpTradeEvent } from '../../types-solana';
import { PUMP_TRADE_EVENT_DISCRIMINATOR, matchesDiscriminator } from '../../constants-solana';

/**
 * Borsh schema for PumpTradeEvent
 * 
 * CRITICAL: The order of fields MUST match exactly the Rust struct definition
 * in the Pump.fun program. Any mismatch will cause deserialization to fail.
 * 
 * Rust struct (from donor repo):
 * ```rust
 * pub struct TradeEvent {
 *     pub mint: Pubkey,
 *     pub sol_amount: u64,
 *     pub token_amount: u64,
 *     pub is_buy: bool,
 *     pub user: Pubkey,
 *     pub timestamp: i64,
 *     pub virtual_sol_reserves: u64,
 *     pub virtual_token_reserves: u64,
 *     pub real_sol_reserves: u64,
 *     pub real_token_reserves: u64,
 *     pub fee_recipient: Pubkey,
 *     pub fee_basis_points: u64,
 *     pub fee: u64,
 *     pub creator: Pubkey,
 *     pub creator_fee_basis_points: u64,
 *     pub creator_fee: u64,
 *     pub track_volume: bool,
 *     pub total_unclaimed_tokens: u64,
 *     pub total_claimed_tokens: u64,
 *     pub current_sol_volume: u64,
 *     pub last_update_timestamp: i64,
 * }
 * ```
 */
const pumpTradeEventSchema = struct([
    publicKey('mint'),
    u64('solAmount'),
    u64('tokenAmount'),
    bool('isBuy'),
    publicKey('user'),
    i64('timestamp'),
    u64('virtualSolReserves'),
    u64('virtualTokenReserves'),
    u64('realSolReserves'),
    u64('realTokenReserves'),
    publicKey('feeRecipient'),
    u64('feeBasisPoints'),
    u64('fee'),
    publicKey('creator'),
    u64('creatorFeeBasisPoints'),
    u64('creatorFee'),
    bool('trackVolume'),
    u64('totalUnclaimedTokens'),
    u64('totalClaimedTokens'),
    u64('currentSolVolume'),
    i64('lastUpdateTimestamp'),
]);

/**
 * Deserialize Pump.fun TradeEvent from instruction data
 * 
 * @param data - Raw instruction data (Buffer)
 * @returns Parsed PumpTradeEvent or null if deserialization fails
 */
export function deserializePumpTradeEvent(data: Buffer): PumpTradeEvent | null {
    try {
        // Step 1: Check discriminator (first 16 bytes for Pump)
        if (!matchesDiscriminator(data, PUMP_TRADE_EVENT_DISCRIMINATOR)) {
            // Not a TradeEvent - this is expected for most instructions
            return null;
        }
        
        // Step 2: Extract event data (skip discriminator)
        const eventData = data.slice(PUMP_TRADE_EVENT_DISCRIMINATOR.length);
        
        // Expected size: 4 * 32 (Pubkeys) + 13 * 8 (u64/i64) + 2 * 1 (bool) = 234 bytes minimum
        if (eventData.length < 230) {
            return null;
        }
        
        // Step 3: Deserialize using Borsh
        const decoded = pumpTradeEventSchema.decode(eventData);
        
        // Convert raw bytes to PublicKey objects
        const event: PumpTradeEvent = {
            mint: new PublicKey(decoded.mint),
            solAmount: decoded.solAmount,
            tokenAmount: decoded.tokenAmount,
            isBuy: decoded.isBuy,
            user: new PublicKey(decoded.user),
            timestamp: decoded.timestamp,
            virtualSolReserves: decoded.virtualSolReserves,
            virtualTokenReserves: decoded.virtualTokenReserves,
            realSolReserves: decoded.realSolReserves,
            realTokenReserves: decoded.realTokenReserves,
            feeRecipient: new PublicKey(decoded.feeRecipient),
            feeBasisPoints: decoded.feeBasisPoints,
            fee: decoded.fee,
            creator: new PublicKey(decoded.creator),
            creatorFeeBasisPoints: decoded.creatorFeeBasisPoints,
            creatorFee: decoded.creatorFee,
            trackVolume: decoded.trackVolume,
            totalUnclaimedTokens: decoded.totalUnclaimedTokens,
            totalClaimedTokens: decoded.totalClaimedTokens,
            currentSolVolume: decoded.currentSolVolume,
            lastUpdateTimestamp: decoded.lastUpdateTimestamp,
        };
        
        return event;
    } catch (error) {
        // Failed to deserialize - not a valid TradeEvent
        return null;
    }
}

/**
 * Check if instruction data contains a Pump.fun TradeEvent
 * 
 * @param data - Raw instruction data
 * @returns true if data starts with Pump TradeEvent discriminator
 */
export function isPumpTradeEvent(data: Buffer): boolean {
    return matchesDiscriminator(data, PUMP_TRADE_EVENT_DISCRIMINATOR);
}

