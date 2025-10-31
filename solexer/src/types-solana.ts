// Solana-specific type definitions for the indexer

import { PublicKey } from '@solana/web3.js';

// Базовые типы Solana
export interface SolanaTransaction {
    signature: string;
    slot: number;
    blockTime: number | null;
    meta: TransactionMeta | null;
    transaction: {
        message: {
            accountKeys: PublicKey[];
            instructions: CompiledInstruction[];
        };
        signatures: string[];
    };
}

export interface CompiledInstruction {
    programIdIndex: number;
    accounts: number[];
    data: string; // base58
}

export interface TransactionMeta {
    err: any | null;
    fee: number;
    innerInstructions: InnerInstruction[];
    preBalances: number[];
    postBalances: number[];
    preTokenBalances?: any[];
    postTokenBalances?: any[];
    logMessages: string[];
}

export interface InnerInstruction {
    index: number;
    instructions: CompiledInstruction[];
}

// Jupiter типы
export interface JupiterSwapEvent {
    amm: PublicKey;
    inputMint: PublicKey;
    inputAmount: bigint;
    outputMint: PublicKey;
    outputAmount: bigint;
}

// Pump.fun типы
export interface PumpTradeEvent {
    mint: PublicKey;
    solAmount: bigint;
    tokenAmount: bigint;
    isBuy: boolean;
    user: PublicKey;
    timestamp: bigint;
    virtualSolReserves: bigint;
    virtualTokenReserves: bigint;
    realSolReserves: bigint;
    realTokenReserves: bigint;
    feeRecipient: PublicKey;
    feeBasisPoints: bigint;
    fee: bigint;
    creator: PublicKey;
    creatorFeeBasisPoints: bigint;
    creatorFee: bigint;
    trackVolume: boolean;
    totalUnclaimedTokens: bigint;
    totalClaimedTokens: bigint;
    currentSolVolume: bigint;
    lastUpdateTimestamp: bigint;
}

// Metadata extraction from Solana transaction
export interface SolanaTransactionMetadata {
    signature: string;
    slot: number;
    blockTime: number;
    signer: string; // Base58 address
}


