"use strict";
/**
 * Pump.fun TradeEvent Deserializer
 *
 * Deserializes Pump.fun TradeEvent from instruction data using Borsh.
 * Based on: workdir/donor_repo/decoders/pumpfun-decoder/
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.deserializePumpTradeEvent = deserializePumpTradeEvent;
exports.isPumpTradeEvent = isPumpTradeEvent;
const borsh_1 = require("@coral-xyz/borsh");
const web3_js_1 = require("@solana/web3.js");
const constants_solana_1 = require("../../constants-solana");
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
const pumpTradeEventSchema = (0, borsh_1.struct)([
    (0, borsh_1.publicKey)('mint'),
    (0, borsh_1.u64)('solAmount'),
    (0, borsh_1.u64)('tokenAmount'),
    (0, borsh_1.bool)('isBuy'),
    (0, borsh_1.publicKey)('user'),
    (0, borsh_1.i64)('timestamp'),
    (0, borsh_1.u64)('virtualSolReserves'),
    (0, borsh_1.u64)('virtualTokenReserves'),
    (0, borsh_1.u64)('realSolReserves'),
    (0, borsh_1.u64)('realTokenReserves'),
    (0, borsh_1.publicKey)('feeRecipient'),
    (0, borsh_1.u64)('feeBasisPoints'),
    (0, borsh_1.u64)('fee'),
    (0, borsh_1.publicKey)('creator'),
    (0, borsh_1.u64)('creatorFeeBasisPoints'),
    (0, borsh_1.u64)('creatorFee'),
    (0, borsh_1.bool)('trackVolume'),
    (0, borsh_1.u64)('totalUnclaimedTokens'),
    (0, borsh_1.u64)('totalClaimedTokens'),
    (0, borsh_1.u64)('currentSolVolume'),
    (0, borsh_1.i64)('lastUpdateTimestamp'),
]);
/**
 * Deserialize Pump.fun TradeEvent from instruction data
 *
 * @param data - Raw instruction data (Buffer)
 * @returns Parsed PumpTradeEvent or null if deserialization fails
 */
function deserializePumpTradeEvent(data) {
    try {
        // Step 1: Check discriminator (first 16 bytes for Pump)
        if (!(0, constants_solana_1.matchesDiscriminator)(data, constants_solana_1.PUMP_TRADE_EVENT_DISCRIMINATOR)) {
            // Not a TradeEvent - this is expected for most instructions
            return null;
        }
        // Step 2: Extract event data (skip discriminator)
        const eventData = data.slice(constants_solana_1.PUMP_TRADE_EVENT_DISCRIMINATOR.length);
        // Expected size: 4 * 32 (Pubkeys) + 13 * 8 (u64/i64) + 2 * 1 (bool) = 234 bytes minimum
        if (eventData.length < 230) {
            return null;
        }
        // Step 3: Deserialize using Borsh
        const decoded = pumpTradeEventSchema.decode(eventData);
        // Convert raw bytes to PublicKey objects
        const event = {
            mint: new web3_js_1.PublicKey(decoded.mint),
            solAmount: decoded.solAmount,
            tokenAmount: decoded.tokenAmount,
            isBuy: decoded.isBuy,
            user: new web3_js_1.PublicKey(decoded.user),
            timestamp: decoded.timestamp,
            virtualSolReserves: decoded.virtualSolReserves,
            virtualTokenReserves: decoded.virtualTokenReserves,
            realSolReserves: decoded.realSolReserves,
            realTokenReserves: decoded.realTokenReserves,
            feeRecipient: new web3_js_1.PublicKey(decoded.feeRecipient),
            feeBasisPoints: decoded.feeBasisPoints,
            fee: decoded.fee,
            creator: new web3_js_1.PublicKey(decoded.creator),
            creatorFeeBasisPoints: decoded.creatorFeeBasisPoints,
            creatorFee: decoded.creatorFee,
            trackVolume: decoded.trackVolume,
            totalUnclaimedTokens: decoded.totalUnclaimedTokens,
            totalClaimedTokens: decoded.totalClaimedTokens,
            currentSolVolume: decoded.currentSolVolume,
            lastUpdateTimestamp: decoded.lastUpdateTimestamp,
        };
        return event;
    }
    catch (error) {
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
function isPumpTradeEvent(data) {
    return (0, constants_solana_1.matchesDiscriminator)(data, constants_solana_1.PUMP_TRADE_EVENT_DISCRIMINATOR);
}
