"use strict";
/**
 * Jupiter SwapEvent Deserializer
 *
 * Deserializes Jupiter V6 SwapEvent from instruction data using Borsh.
 * Based on: workdir/donor_repo/decoders/jupiter-swap-decoder/
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.deserializeJupiterSwapEvent = deserializeJupiterSwapEvent;
exports.isJupiterSwapEvent = isJupiterSwapEvent;
const borsh_1 = require("@coral-xyz/borsh");
const web3_js_1 = require("@solana/web3.js");
const constants_solana_1 = require("../../constants-solana");
/**
 * Borsh schema for JupiterSwapEvent
 *
 * CRITICAL: The order of fields MUST match exactly the Rust struct definition
 * in the Jupiter program. Any mismatch will cause deserialization to fail.
 *
 * Rust struct (from donor repo):
 * ```rust
 * pub struct SwapEvent {
 *     pub amm: Pubkey,
 *     pub input_mint: Pubkey,
 *     pub input_amount: u64,
 *     pub output_mint: Pubkey,
 *     pub output_amount: u64,
 * }
 * ```
 */
const jupiterSwapEventSchema = (0, borsh_1.struct)([
    (0, borsh_1.publicKey)('amm'),
    (0, borsh_1.publicKey)('inputMint'),
    (0, borsh_1.u64)('inputAmount'),
    (0, borsh_1.publicKey)('outputMint'),
    (0, borsh_1.u64)('outputAmount'),
]);
/**
 * Deserialize Jupiter SwapEvent from instruction data
 *
 * @param data - Raw instruction data (Buffer)
 * @returns Parsed JupiterSwapEvent or null if deserialization fails
 */
function deserializeJupiterSwapEvent(data) {
    try {
        // Check discriminator (first 16 bytes)
        // CRITICAL: Must check full 16 bytes! FeeEvent and SwapsEvent share the first 8 bytes
        if (!(0, constants_solana_1.matchesDiscriminator)(data, constants_solana_1.JUPITER_SWAP_EVENT_DISCRIMINATOR)) {
            return null;
        }
        // Extract event data (skip 16-byte discriminator)
        const eventData = data.slice(constants_solana_1.JUPITER_SWAP_EVENT_DISCRIMINATOR.length);
        // SwapEvent size: 32 (amm) + 32 (inputMint) + 8 (inputAmount) + 32 (outputMint) + 8 (outputAmount) = 112 bytes
        if (eventData.length < 112) {
            return null;
        }
        // Deserialize using Borsh
        const decoded = jupiterSwapEventSchema.decode(eventData);
        // Convert raw bytes to PublicKey objects
        const event = {
            amm: new web3_js_1.PublicKey(decoded.amm),
            inputMint: new web3_js_1.PublicKey(decoded.inputMint),
            inputAmount: decoded.inputAmount,
            outputMint: new web3_js_1.PublicKey(decoded.outputMint),
            outputAmount: decoded.outputAmount,
        };
        return event;
    }
    catch (error) {
        return null;
    }
}
/**
 * Check if instruction data contains a Jupiter SwapEvent
 *
 * @param data - Raw instruction data
 * @returns true if data starts with Jupiter SwapEvent discriminator
 */
function isJupiterSwapEvent(data) {
    return (0, constants_solana_1.matchesDiscriminator)(data, constants_solana_1.JUPITER_SWAP_EVENT_DISCRIMINATOR);
}
