// Type definitions for the indexer

export interface BlockRow {
    number: number;
    hash: string;
    parent_hash: string;
    nonce: string | null;
    sha3_uncles: string;
    logs_bloom: string;
    transactions_root: string;
    state_root: string;
    receipts_root: string;
    miner: string;
    difficulty: number;
    total_difficulty: number;
    size: number;
    extra_data: string;
    gas_limit: number;
    gas_used: number;
    l1_block_number: number;
    base_fee_per_gas: string | null;
    timestamp: number;
    transaction_count: number;
}

export interface TransactionRow {
    hash: string;
    nonce: number;
    block_hash: string;
    block_number: number;
    transaction_index: number;
    from_address: string;
    to_address: string | null;
    value: string;
    gas: bigint;
    gas_price: bigint | null;
    input: string;
    block_timestamp: bigint;
    max_fee_per_gas: bigint | null;
    max_priority_fee_per_gas: bigint | null;
    transaction_type: number | null;
    receipt_cumulative_gas_used: bigint | null;
    receipt_gas_used: bigint | null;
    receipt_contract_address: string | null;
    receipt_root: string | null;
    receipt_status: number | null;
    receipt_effective_gas_price: bigint | null;
    receipt_logs_count: number | null;
    is_reorged: boolean;
}

export interface LogRow {
    log_index: number;
    transaction_hash: string;
    transaction_index: number;
    block_hash: string;
    block_number: number;
    block_timestamp: number;
    address: string;
    data: string;
    topics: string[];
    is_reorged: boolean;
}

export interface Transfer {
    token_address: string;
    token_standard: 'ERC-20' | 'ERC-721' | 'ERC-1155';
    from_address: string;
    to_address: string;
    value: string;
    transaction_hash: string;
    log_index: number;
    block_timestamp: number;
    block_number: number;
    block_hash: string;
    operator_address: string | null;
    token_id: string | null;
}

export interface BalanceChange {
    token_address: string;
    holder_address: string;
    token_id: string | null;
    amount: string;
    block_number: number;
    block_timestamp: number;
    token_standard: string;
    transaction_hash: string;
    log_index: number;
}

export interface NativeBalance {
    address: string;
    block_number: number;
    block_hash: string;
    block_timestamp: number;
    value: string;
    is_reorged: number;
}

export interface DexPool {
    pool_address: string;
    factory_address: string;
    token0_address: string;
    token1_address: string;
    amm: string; // 'uniswap_v2', 'burning_meme', etc.
    created_block_number: number;
    created_block_timestamp: number;
    is_active: boolean;
}

export interface DexPoolEntity {
    address: string;
    factory_address: string;
    token_addresses: string[];
    lp_token_addresses: string[];
    fee: number;
    underlying_token_addresses: string[];
}

export interface DexTrade {
    token_amounts: string[];
    pool_address: string;
    transaction_hash: string;
    log_index: number;
    block_number: number;
    event_type: 'swap' | 'burn' | 'mint';
    token_reserves: string[];
    token_prices: string[][];
    token_addresses: string[];
    lp_token_address: string;
    amm: string;
    wallet_address: string;
    block_hash: string;
    block_timestamp: number;
    // Extended fields to match expected schema
    factory_address?: string;
    transaction_type?: string; // e.g. 'swap'
    is_reorged?: number; // 0 or 1
    swap_type?: 'buy' | 'sell' | string;
    // Derived amounts and prices in native/stable terms
    amounts?: string[]; // normalized human-readable amounts, same order as token_addresses
    amount_native?: string; // signed amount for native token in trade
    amount_stable?: string; // native amount converted to stable using configured rate
    prices_native?: string[]; // price of each token in native
    prices_stable?: string[]; // price of each token in stable
    reserves?: string[]; // normalized reserves (alias of token_reserves)
    reserves_native?: string[]; // reserves converted to native value
    reserves_stable?: string[]; // reserves converted to stable value
}

export interface Token {
    address: string;
    symbol: string;
    name: string;
    decimals: number;
    total_supply: string;
    block_number: number;
    block_timestamp: number;
    transaction_hash: string;
    is_erc20?: boolean;
    is_erc721?: boolean;
}

export interface BatchManager {
    blocks: BlockRow[];
    transactions: TransactionRow[];
    logs: LogRow[];
    transfers: Transfer[];
    nativeBalances: NativeBalance[];
    balanceIncreases: BalanceChange[];
    balanceDecreases: BalanceChange[];
    snapshots: any[];
    dexTrades: DexTrade[];
    dexPools: DexPool[];
    dexPoolEntities: DexPoolEntity[];
    tokens: Token[];
} 