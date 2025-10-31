/**
 * Jupiter SwapEvent Deserializer
 * 
 * Deserializes Jupiter V6 SwapEvent from instruction data using Borsh.
 * Based on: workdir/donor_repo/decoders/jupiter-swap-decoder/
 */

import { struct, u64, publicKey } from '@coral-xyz/borsh';
import { PublicKey } from '@solana/web3.js';
import { JupiterSwapEvent } from '../../types-solana';
import { JUPITER_SWAP_EVENT_DISCRIMINATOR, matchesDiscriminator } from '../../constants-solana';

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
const jupiterSwapEventSchema = struct([
    publicKey('amm'),
    publicKey('inputMint'),
    u64('inputAmount'),
    publicKey('outputMint'),
    u64('outputAmount'),
]);

/**
 * Deserialize Jupiter SwapEvent from instruction data
 * 
 * @param data - Raw instruction data (Buffer)
 * @returns Parsed JupiterSwapEvent or null if deserialization fails
 */
export function deserializeJupiterSwapEvent(data: Buffer): JupiterSwapEvent | null {
    try {
        // Check discriminator (first 16 bytes)
        // CRITICAL: Must check full 16 bytes! FeeEvent and SwapsEvent share the first 8 bytes
        if (!matchesDiscriminator(data, JUPITER_SWAP_EVENT_DISCRIMINATOR)) {
            return null;
        }
        
        // Extract event data (skip 16-byte discriminator)
        const eventData = data.slice(JUPITER_SWAP_EVENT_DISCRIMINATOR.length);
        
        // SwapEvent size: 32 (amm) + 32 (inputMint) + 8 (inputAmount) + 32 (outputMint) + 8 (outputAmount) = 112 bytes
        if (eventData.length < 112) {
            return null;
        }
        
        // Deserialize using Borsh
        const decoded = jupiterSwapEventSchema.decode(eventData);
        
        // Convert raw bytes to PublicKey objects
        const event: JupiterSwapEvent = {
            amm: new PublicKey(decoded.amm),
            inputMint: new PublicKey(decoded.inputMint),
            inputAmount: decoded.inputAmount,
            outputMint: new PublicKey(decoded.outputMint),
            outputAmount: decoded.outputAmount,
        };
        
        return event;
    } catch (error) {
        return null;
    }
}

/**
 * Check if instruction data contains a Jupiter SwapEvent
 * 
 * @param data - Raw instruction data
 * @returns true if data starts with Jupiter SwapEvent discriminator
 */
export function isJupiterSwapEvent(data: Buffer): boolean {
    return matchesDiscriminator(data, JUPITER_SWAP_EVENT_DISCRIMINATOR);
}

