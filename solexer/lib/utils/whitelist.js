"use strict";
/**
 * Whitelist Utility
 *
 * Loads and checks token addresses against a whitelist file.
 * Only trades involving whitelisted tokens will be processed.
 */
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.loadWhitelist = loadWhitelist;
exports.isTokenWhitelisted = isTokenWhitelisted;
exports.hasWhitelistedToken = hasWhitelistedToken;
exports.getWhitelistSize = getWhitelistSize;
exports.resetWhitelist = resetWhitelist;
const fs_1 = __importDefault(require("fs"));
const path_1 = __importDefault(require("path"));
let whitelist = null;
// Base trading pair tokens that are always allowed
// These are NOT filtered - they can be on either side of a trade
const BASE_PAIRS = new Set([
    'So11111111111111111111111111111111111111112', // Wrapped SOL
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v', // USDC
]);
/**
 * Load whitelist from file
 *
 * @param whitelistPath - Path to whitelist.txt file
 * @returns Set of whitelisted token addresses
 */
function loadWhitelist(whitelistPath) {
    if (whitelist) {
        return whitelist;
    }
    const filePath = whitelistPath || path_1.default.join(__dirname, '../../whitelist.txt');
    try {
        if (!fs_1.default.existsSync(filePath)) {
            console.warn(`⚠️  Whitelist file not found at ${filePath}. Processing all tokens.`);
            whitelist = new Set();
            return whitelist;
        }
        const content = fs_1.default.readFileSync(filePath, 'utf-8');
        const addresses = content
            .split('\n')
            .map(addr => addr.trim())
            .filter(addr => addr.length > 0);
        whitelist = new Set(addresses);
        console.log(`✅ Loaded whitelist with ${whitelist.size} token addresses`);
        return whitelist;
    }
    catch (error) {
        console.error(`❌ Error loading whitelist from ${filePath}:`, error);
        whitelist = new Set();
        return whitelist;
    }
}
/**
 * Check if a token is whitelisted
 *
 * @param tokenAddress - Token address to check
 * @returns True if token is whitelisted (or whitelist is empty/disabled)
 */
function isTokenWhitelisted(tokenAddress) {
    if (!whitelist) {
        loadWhitelist();
    }
    // If whitelist is empty, allow all tokens
    if (whitelist.size === 0) {
        return true;
    }
    return whitelist.has(tokenAddress);
}
/**
 * Check if ANY token in the list is whitelisted (excluding base pairs)
 *
 * This is the smart filter: a trade passes if at least one token
 * (excluding common base pairs like SOL/USDC) is in the whitelist.
 *
 * @param tokenAddresses - Array of token addresses
 * @returns True if at least one non-base-pair token is whitelisted
 */
function hasWhitelistedToken(tokenAddresses) {
    if (!whitelist) {
        loadWhitelist();
    }
    // If whitelist is empty, allow all tokens
    if (whitelist.size === 0) {
        return true;
    }
    // Check if at least one token (excluding base pairs) is whitelisted
    for (const addr of tokenAddresses) {
        // Skip base pairs in the check
        if (BASE_PAIRS.has(addr)) {
            continue;
        }
        // If a non-base-pair token is whitelisted, include the trade
        if (whitelist.has(addr)) {
            return true;
        }
    }
    // No whitelisted tokens found (only base pairs or non-whitelisted tokens)
    return false;
}
/**
 * Get the number of whitelisted tokens
 *
 * @returns Number of tokens in whitelist
 */
function getWhitelistSize() {
    if (!whitelist) {
        loadWhitelist();
    }
    return whitelist.size;
}
/**
 * Reset whitelist (for testing or reloading)
 */
function resetWhitelist() {
    whitelist = null;
}
