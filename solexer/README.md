# Solana DEX Indexer

A high-performance Solana blockchain indexer built with Subsquid that indexes DEX trades from Jupiter and Pump.fun. Data is stored in ClickHouse for efficient querying and analytics.

---

## ⚡ Quick Start

### Prerequisites
- Node.js 20.x+
- Docker & Docker Compose
- npm

### Get Running in 5 Minutes

```bash
# 1. Navigate to indexer directory
cd indexer

# 2. Install dependencies
npm install

# 3. Start ClickHouse database
docker-compose up -d clickhouse

# 4. Run database migrations
cd db
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r ../req.txt
alembic upgrade head
cd ..

# 5. Build TypeScript
npm run build

# 6. Start the indexer
npm run start:solana
```

### Verify It's Working

```bash
# Check indexed trades
docker exec indexer-clickhouse-1 clickhouse-client --query \
  "SELECT COUNT(*) FROM solana_indexer.dex_trades WHERE amm IN ('jupiter_v6', 'pump')"

# View recent trades
docker exec indexer-clickhouse-1 clickhouse-client --query \
  "SELECT amm, swap_type, block_number, transaction_hash FROM solana_indexer.dex_trades ORDER BY block_number DESC LIMIT 10"
```

---

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Setup & Configuration](#setup--configuration)
- [Database Management](#database-management)
- [How It Works](#how-it-works)
- [Development](#development)
- [Token Whitelist](#token-whitelist)
- [Production Deployment](#production-deployment)
- [Troubleshooting](#troubleshooting)
- [Performance](#performance)

---

## Overview

This indexer extracts and processes DEX trade data from Solana blockchain:

### Supported Protocols
- **Jupiter V6**: DEX aggregator with multi-hop routing
- **Jupiter V4**: Legacy DEX aggregator  
- **Pump.fun**: Bonding curve token launches

### Data Stored
- Trade transactions (swaps, amounts, prices)
- Pool addresses and reserves
- Wallet addresses
- Token balances (pre/post trade)
- Block metadata (height, slot, timestamp)

All data flows into ClickHouse for high-performance analytics across millions of trades.

---

## Architecture

### Tech Stack

```
Subsquid Solana Gateway → TypeScript Processor → ClickHouse Database
                              ↓
                      Event Parsers (Borsh)
                              ↓
                     Jupiter | Pump.fun
```

**Core Technologies:**
- **Data Source**: [@subsquid/solana-stream](https://github.com/subsquid/squid-sdk) - Efficient Solana data streaming
- **Deserialization**: [@subsquid/borsh](https://www.npmjs.com/package/@subsquid/borsh) - Binary event parsing
- **Database**: ClickHouse - Columnar database for analytics
- **Language**: TypeScript - Type-safe processing

### Project Structure

```
indexer/
├── src/
│   ├── main-solana.ts              # Main processor entry point
│   ├── config-solana.ts            # Configuration management
│   ├── constants-solana.ts         # Program IDs and constants
│   ├── state-manager.ts            # Resume/checkpoint logic
│   ├── parsers/solana/
│   │   ├── jupiter-parser.ts       # Jupiter swap event parser
│   │   ├── jupiter-deserializer.ts # Jupiter Borsh schemas
│   │   ├── pump-parser.ts          # Pump.fun trade parser
│   │   └── pump-deserializer.ts    # Pump.fun Borsh schemas
│   ├── utils/
│   │   └── whitelist.ts            # Token filtering logic
│   └── clickhouseClient/
│       ├── clickhouseClient.ts     # Database operations
│       └── healthCheck.ts          # Connection validation
├── db/migrations/                  # Alembic migrations
├── whitelist.txt                   # Token addresses to index
├── docker-compose.yaml             # Local deployment
└── package.json                    # Dependencies & scripts
```

### Data Flow

```
1. Subsquid Gateway Streams Blocks
         ↓
2. Filter Instructions (Jupiter/Pump program IDs)
         ↓
3. Extract Inner Instructions (CPI events)
         ↓
4. Check Event Discriminators (8-16 byte prefix)
         ↓
5. Deserialize with Borsh (SwapEvent/TradeEvent)
         ↓
6. Map to DexTrade Schema
         ↓
7. Apply Token Whitelist Filter
         ↓
8. Batch Insert to ClickHouse
         ↓
9. Update State (checkpoint for resume)
```

---

## Features

### Core Capabilities
✅ **Multi-Protocol Support** - Jupiter V6/V4 and Pump.fun in unified schema  
✅ **State Management** - Automatic resume from last processed block  
✅ **Token Filtering** - Whitelist-based trade filtering  
✅ **High Performance** - Processes 100+ blocks/second  
✅ **Graceful Shutdown** - Ensures all data flushed before exit  
✅ **Error Recovery** - Automatic retry on transient failures  
✅ **Docker Ready** - Complete containerized deployment  

### Solana-Specific Features
- **Height-Based Indexing**: Uses Subsquid's block height (~slot - 22M) for consistency
- **Inner Instruction Processing**: Parses CPI events where DEX protocols emit swap data
- **Borsh Deserialization**: Native Solana event format decoding
- **Multi-Hop Swaps**: Tracks individual swap legs in Jupiter routes
- **Reserve Tracking**: Captures pool reserves from Pump.fun events

---

## Setup & Configuration

### Installation

**Step 1: Install Node.js Dependencies**
```bash
cd indexer
npm install
```

**Step 2: Start ClickHouse**
```bash
docker-compose up -d clickhouse

# Verify it's running
docker ps | grep clickhouse
```

**Step 3: Setup Database Migrations**
```bash
cd db

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Alembic and dependencies
pip install -r ../req.txt
```

**Step 4: Run Migrations**
```bash
# Still in db/ directory with venv activated
alembic upgrade head

# Verify tables created
docker exec indexer-clickhouse-1 clickhouse-client --query "SHOW TABLES FROM solana_indexer"
```

**Step 5: Configure Environment**

Create configuration file based on your needs:

```bash
# For local development (uses default settings)
cp configs/base.env .env.solana

# Or create custom .env.solana with your settings
```

**Step 6: Build and Run**
```bash
# Build TypeScript
npm run build

# Start indexer
npm run start:solana

# Or run with ts-node for development
npm run dev:solana:ts
```

### Configuration File (.env.solana)

The indexer uses environment variables for configuration. Here's a complete example:

```bash
# ===== SOLANA NETWORK =====
# Subsquid Gateway (required)
SOLANA_GATEWAY_URL=https://v2.archive.subsquid.io/network/solana-mainnet

# RPC Endpoint (for real-time sync & metadata)
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_RPC_RATE_LIMIT=10

# ===== BLOCK RANGE =====
# Start height (NOT slot!)
# Heights are ~22M less than slots
# Example: Slot 280,000,000 ≈ Height 258,000,000
SOLANA_START_HEIGHT=258000000

# Optional end height (leave unset for continuous)
# SOLANA_END_HEIGHT=

# ===== PROGRAM IDs (DO NOT CHANGE) =====
JUPITER_V6_PROGRAM_ID=JUP6LkbZbjS1jKKwapdHNy74zcZ3tLUZoi5QNyVTaV4
JUPITER_V4_PROGRAM_ID=JUP4Fb2cqiRUcaTHdrPC8h2gNsA2ETXiPDD33WcGuJB
PUMP_PROGRAM_ID=6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P

# ===== CLICKHOUSE =====
CLICKHOUSE_HOST=http://localhost:8123
CLICKHOUSE_USER=default
CLICKHOUSE_PASSWORD=PASS
CLICKHOUSE_DATABASE=solana_indexer

# ===== PERFORMANCE =====
SOLANA_BATCH_SIZE=100
CHAIN_ID=solana-mainnet
```

### Important Configuration Notes

**Block Heights vs Slots:**
- Subsquid uses **block heights**, not slots!
- Height ≈ Slot - 22,000,000 (approximate)
- The indexer calculates exact offset from first block
- Always configure `SOLANA_START_HEIGHT` not `SOLANA_START_SLOT`

**RPC Provider Recommendations:**

| Provider | Free Tier | Rate Limit | Best For |
|----------|-----------|------------|----------|
| Public Endpoint | ✅ Yes | ~10 req/s | Testing only |
| [Helius](https://helius.dev/) | ✅ Yes | 100+ req/s | **Recommended** |
| [Alchemy](https://alchemy.com/) | ✅ Yes | 100+ req/s | Production |
| [QuickNode](https://quicknode.com/) | ❌ No | High | Enterprise |

---

## Database Management

### Migrations

The indexer uses Alembic for database schema management.

**Apply All Migrations:**
```bash
cd db
source venv/bin/activate  # Activate Python venv
alembic upgrade head
```

**Check Migration Status:**
```bash
alembic current
alembic history
```

**Rollback One Migration:**
```bash
alembic downgrade -1
```

### Database Schema

**Main Tables:**

| Table | Purpose | Engine |
|-------|---------|--------|
| `dex_trades` | All DEX trades (Jupiter + Pump) | MergeTree |
| `solana_indexer_state` | Checkpoint/resume state | ReplacingMergeTree |

**dex_trades Schema:**
```sql
CREATE TABLE solana_indexer.dex_trades (
    block_number UInt64,          -- Block height
    block_hash String,            -- Always empty on Solana
    block_timestamp UInt32,       -- Unix timestamp
    transaction_hash String,      -- Transaction signature
    log_index UInt32,             -- Instruction index
    transaction_type String,      -- 'swap'
    swap_type String,             -- 'buy' or 'sell'
    amm String,                   -- 'jupiter_v6', 'jupiter_v4', 'pump'
    token_addresses Array(String), -- [tokenIn, tokenOut]
    amounts Array(Float64),       -- [amountIn, amountOut]
    amount_stable Float64,        -- Amount in USDC terms
    amount_native Float64,        -- Amount in SOL terms
    prices_native Array(Float64), -- Price in SOL
    pool_address String,          -- Pool/curve address
    wallet_address String,        -- Trader wallet
    reserves Array(Float64),      -- Pool reserves
    is_reorged UInt8              -- Always 0 (Solana doesn't reorg)
) ENGINE = MergeTree()
ORDER BY (block_number, transaction_hash, log_index);
```

**solana_indexer_state Schema:**
```sql
CREATE TABLE solana_indexer.solana_indexer_state (
    state_key String,             -- 'last_processed_block'
    state_value String,           -- Block height as string
    chain String,                 -- 'solana-mainnet'
    updated_at DateTime,          -- Last update time
    version UInt64                -- Version for ReplacingMergeTree
) ENGINE = ReplacingMergeTree(version)
ORDER BY (chain, state_key);
```

### Useful Queries

**Check Indexing Progress:**
```sql
SELECT 
    state_value as last_height,
    updated_at
FROM solana_indexer.solana_indexer_state FINAL
WHERE state_key = 'last_processed_block'
  AND chain = 'solana-mainnet';
```

**Trade Statistics:**
```sql
SELECT 
    amm,
    COUNT(*) as trade_count,
    SUM(amount_native) as total_sol_volume
FROM solana_indexer.dex_trades
WHERE block_timestamp > toUnixTimestamp(now() - INTERVAL 1 DAY)
GROUP BY amm;
```

**Recent Trades:**
```sql
SELECT 
    transaction_hash,
    amm,
    swap_type,
    token_addresses,
    amounts,
    wallet_address
FROM solana_indexer.dex_trades
ORDER BY block_number DESC
LIMIT 20;
```

---

## How It Works

### Solana Event Model

Unlike EVM chains that emit logs, Solana programs emit events as **inner instructions** (CPIs - Cross-Program Invocations).

**Event Detection Flow:**

1. **Top-Level Instruction**: User calls Jupiter/Pump program
2. **CPI Emission**: Program creates special inner instruction with event data
3. **Discriminator Check**: First 8-16 bytes identify event type
4. **Borsh Decode**: Deserialize remaining bytes using schema
5. **Trade Extraction**: Map event fields to DexTrade format

### Jupiter Parsing

**SwapEvent Structure:**
```typescript
// Discriminator: 0xe445a52e51cb9a1d40c6cde8260871e2 (16 bytes)
{
  amm: PublicKey,           // Pool address (32 bytes)
  inputMint: PublicKey,     // Input token (32 bytes)
  inputAmount: u64,         // Amount in (8 bytes)
  outputMint: PublicKey,    // Output token (32 bytes)
  outputAmount: u64         // Amount out (8 bytes)
}
```

**Why 16-byte discriminator?**
Multiple Jupiter events share the first 8 bytes:
- SwapEvent: `0xe445a52e51cb9a1d40c6cde8260871e2`
- FeeEvent: `0xe445a52e51cb9a1d494f4e7fb8d50ddc`
- SwapsEvent: `0xe445a52e51cb9a1d982f4eebc0606e6a`

We must check all 16 bytes to avoid false positives.

### Pump.fun Parsing

**TradeEvent Structure:**
```typescript
// Discriminator: 0xe445a52e51cb9a1dbddb7fd34ee661ee (16 bytes)
{
  mint: PublicKey,          // Token address
  solAmount: u64,           // SOL amount
  tokenAmount: u64,         // Token amount
  isBuy: bool,              // true = buy, false = sell
  user: PublicKey,          // Trader wallet
  timestamp: i64,           // Trade timestamp
  realSolReserves: u64,     // Pool SOL reserves
  realTokenReserves: u64,   // Pool token reserves
  virtualSolReserves: u64,  // Virtual SOL (for pricing)
  virtualTokenReserves: u64 // Virtual tokens (for pricing)
}
```

**Key Insight**: Pump.fun events contain ALL necessary data including:
- User wallet (Jupiter doesn't provide this!)
- Pool reserves (for calculating slippage)
- Precise timestamp (not just block time)

### Borsh Deserialization

Borsh (Binary Object Representation Serializer for Hashing) is Solana's standard serialization format:

**Rules:**
1. All integers are little-endian
2. PublicKeys are 32 bytes
3. Booleans are 1 byte (0x00 or 0x01)
4. **Field order MUST match Rust struct exactly**

**Example:**
```typescript
// Rust struct (program)
pub struct SwapEvent {
    pub amm: Pubkey,          // bytes 0-31
    pub input_mint: Pubkey,   // bytes 32-63
    pub input_amount: u64,    // bytes 64-71
    pub output_mint: Pubkey,  // bytes 72-103
    pub output_amount: u64,   // bytes 104-111
}

// TypeScript deserializer (indexer)
const swapEvent = borsh.struct([
    borsh.publicKey('amm'),
    borsh.publicKey('inputMint'),
    borsh.u64('inputAmount'),
    borsh.publicKey('outputMint'),
    borsh.u64('outputAmount'),
]);
```

Order mismatch = corrupted data!

---

## Development

### Available Scripts

```bash
# Build
npm run build              # Compile TypeScript → lib/
npm run clean              # Remove lib/ directory
npm run rebuild            # Clean + build

# Run
npm run start:solana       # Run compiled JS
npm run dev:solana:ts      # Run with ts-node (development)

# Database
cd db
alembic upgrade head       # Run migrations
alembic downgrade -1       # Rollback one
alembic history            # Show migrations

# Docker
npm run docker:up          # Start services
npm run docker:down        # Stop services
npm run docker:logs        # View logs
npm run docker:build       # Build image
```

### Adding New DEX Protocols

**Step 1: Define Constants**
```typescript
// src/constants-solana.ts
export const NEW_DEX_PROGRAM_ID = 'ProgramId...';
```

**Step 2: Create Deserializer**
```typescript
// src/parsers/solana/newdex-deserializer.ts
import { borsh } from '@subsquid/borsh';

const TRADE_EVENT_DISCRIMINATOR = Buffer.from([/* 8-16 bytes */]);

const tradeEventSchema = borsh.struct([
    borsh.publicKey('tokenA'),
    borsh.u64('amountA'),
    // ... more fields
]);

export function deserializeNewDexEvent(data: Buffer): any | null {
    if (!data.subarray(0, 8).equals(TRADE_EVENT_DISCRIMINATOR.subarray(0, 8))) {
        return null;
    }
    return tradeEventSchema.decode(data.subarray(8));
}
```

**Step 3: Create Parser**
```typescript
// src/parsers/solana/newdex-parser.ts
export async function parseNewDexTransaction(tx: SolanaTransaction): Promise<DexTrade[]> {
    const trades: DexTrade[] = [];
    
    // Find top-level instructions
    for (let i = 0; i < tx.transaction.message.instructions.length; i++) {
        const instruction = tx.transaction.message.instructions[i];
        const programId = tx.transaction.message.accountKeys[instruction.programIdIndex]?.toBase58();
        
        if (programId !== NEW_DEX_PROGRAM_ID) continue;
        
        // Get inner instructions
        const innerInstructions = tx.meta.innerInstructions?.find(inner => inner.index === i);
        if (!innerInstructions) continue;
        
        // Parse events
        for (const innerIx of innerInstructions.instructions) {
            const data = bs58.decode(innerIx.data);
            const event = deserializeNewDexEvent(Buffer.from(data));
            
            if (event) {
                trades.push(convertToDexTrade(event, tx, i));
            }
        }
    }
    
    return trades;
}
```

**Step 4: Integrate into Main Processor**
```typescript
// src/main-solana.ts
import { parseNewDexTransaction } from './parsers/solana/newdex-parser';
import { NEW_DEX_PROGRAM_ID } from './constants-solana';

// Add to program IDs
const programIds = [
    JUPITER_V6_PROGRAM_ID,
    PUMP_PROGRAM_ID,
    NEW_DEX_PROGRAM_ID  // <-- Add here
];

// Add to parsing logic
if (ins.programId === NEW_DEX_PROGRAM_ID) {
    const trades = await parseNewDexTransaction(solanaTransaction);
    allTrades.push(...trades);
}
```

### Testing

**Test Individual Transactions:**
```typescript
// Create test file: src/test-newdex.ts
import { parseNewDexTransaction } from './parsers/solana/newdex-parser';

async function test() {
    const tx = /* fetch from RPC */;
    const trades = await parseNewDexTransaction(tx);
    console.log('Trades found:', trades);
}

test();
```

```bash
ts-node src/test-newdex.ts
```

---

## Token Whitelist

The indexer supports filtering trades to only index specific tokens.

### How It Works

**Whitelist Logic:**
1. Load token addresses from `whitelist.txt`
2. For each trade, check if ANY token (excluding SOL/USDC) is whitelisted
3. If yes → index the trade
4. If no → skip the trade

**Base Pairs (Always Allowed):**
- `So11111111111111111111111111111111111111112` (Wrapped SOL)
- `EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v` (USDC)

### Setup Whitelist

**Method 1: Manual Creation**
```bash
# Create whitelist.txt with one token address per line
cat > whitelist.txt <<EOF
TokenAddress1111111111111111111111111111
TokenAddress2222222222222222222222222222
TokenAddress3333333333333333333333333333
EOF
```

**Method 2: From CSV**
The repository includes a tool to generate whitelist from token lists:

```bash
# Convert CSV to whitelist
node parse-csv-to-whitelist.js

# This reads SOLANA_tokens_2025_10_23.csv
# and generates whitelist.txt
```

### Disable Whitelist

To index ALL trades (no filtering):

```bash
# Empty the whitelist file
echo "" > whitelist.txt

# Or delete it
rm whitelist.txt
```

If `whitelist.txt` is empty or missing, ALL trades are indexed.

---

## Production Deployment

### Docker Deployment

**Step 1: Configure Environment**
```bash
# Create production config
cat > .env.solana.prod <<EOF
SOLANA_RPC_URL=https://rpc.helius.xyz/?api-key=YOUR_KEY
SOLANA_START_HEIGHT=258000000
CLICKHOUSE_HOST=http://clickhouse:8123
CLICKHOUSE_PASSWORD=SecurePassword123
EOF
```

**Step 2: Update docker-compose.yaml**
```yaml
services:
  clickhouse:
    image: clickhouse/clickhouse-server:latest
    environment:
      CLICKHOUSE_PASSWORD: SecurePassword123
    volumes:
      - clickhouse_data:/var/lib/clickhouse
      - ./clickhouse-config.xml:/etc/clickhouse-server/config.d/custom.xml
    restart: unless-stopped

  indexer:
    build: .
    env_file: .env.solana.prod
    depends_on:
      - clickhouse
    restart: unless-stopped
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "3"

volumes:
  clickhouse_data:
```

**Step 3: Deploy**
```bash
# Build and start
docker-compose up -d

# Run migrations
docker-compose exec indexer sh -c "cd db && alembic upgrade head"

# Check logs
docker-compose logs -f indexer
```

### Kubernetes/Helm

**Prerequisites:**
- Kubernetes cluster
- Helm 3+
- External ClickHouse cluster (or deploy with indexer)

**Deployment:**
```bash
# Navigate to helm directory
cd ../helm/charts/squid-indexer

# Install for development
helm install solana-indexer . \
  -f values-dev.yaml \
  --set image.tag=latest

# Install for production
helm install solana-indexer . \
  -f values-prod.yaml \
  --set externalClickhouse.password="SecurePassword" \
  --set solana.rpcUrl="https://rpc.helius.xyz/?api-key=KEY"
```

### Production Checklist

**Security:**
- [ ] Change ClickHouse default password
- [ ] Use secrets management (Kubernetes secrets, AWS Secrets Manager)
- [ ] Configure network policies (restrict ClickHouse access)
- [ ] Use paid RPC provider with API key
- [ ] Enable TLS for ClickHouse connections

**Performance:**
- [ ] Tune `SOLANA_BATCH_SIZE` (start with 100, increase to 500+)
- [ ] Monitor ClickHouse memory/CPU usage
- [ ] Configure autoscaling (horizontal pod autoscaling)
- [ ] Set appropriate resource limits in k8s

**Monitoring:**
- [ ] Set up log aggregation (ELK, Loki, CloudWatch)
- [ ] Monitor indexer health (liveness/readiness probes)
- [ ] Track processing metrics (blocks/sec, trades/sec)
- [ ] Configure alerting (PagerDuty, Slack)

**Backup:**
- [ ] Regular ClickHouse data backups
- [ ] Backup state table separately
- [ ] Version control for configurations
- [ ] Document disaster recovery procedure

### Environment Configurations

**Development:**
```bash
SOLANA_START_HEIGHT=258000000
SOLANA_END_HEIGHT=258010000  # Limited range for testing
SOLANA_BATCH_SIZE=10
```

**Staging:**
```bash
SOLANA_RPC_URL=https://api.devnet.solana.com
SOLANA_START_HEIGHT=258000000
SOLANA_BATCH_SIZE=100
```

**Production:**
```bash
SOLANA_RPC_URL=https://rpc.helius.xyz/?api-key=YOUR_KEY
SOLANA_RPC_RATE_LIMIT=100
SOLANA_START_HEIGHT=258000000
SOLANA_BATCH_SIZE=500
# No END_HEIGHT = continuous indexing
```

**Historical Backfill:**
```bash
SOLANA_START_HEIGHT=200000000  # Older blocks
SOLANA_END_HEIGHT=258000000    # Up to current
SOLANA_BATCH_SIZE=1000         # Large batches
```

---

## Troubleshooting

### Common Issues

#### "Table doesn't exist" Error

**Problem:** Migration not run

**Solution:**
```bash
cd db
source venv/bin/activate
alembic upgrade head

# Verify
docker exec indexer-clickhouse-1 clickhouse-client --query "SHOW TABLES FROM solana_indexer"
```

#### No Trades Found

**Symptoms:** Indexer runs but `dex_trades` table is empty

**Checks:**
```bash
# 1. Verify height range
# Heights should be < 365M (slots are ~22M higher)
echo $SOLANA_START_HEIGHT

# 2. Check whitelist
cat whitelist.txt  # Should have tokens or be empty

# 3. Verify program IDs
# Compare with actual program IDs on Solana
```

#### "Slot vs Height" Confusion

**Problem:** Configured SLOT instead of HEIGHT

**Symptoms:**
- Error: "No blocks found"
- Indexer immediately finishes

**Solution:**
```bash
# Convert slot to height
# Height = Slot - 22,000,000 (approximate)

# Example:
# Slot: 280,000,000
# Height: 258,000,000

# Update config
export SOLANA_START_HEIGHT=258000000
```

#### ClickHouse Connection Failed

**Symptoms:**
```
❌ ClickHouse connection failed
Error: connect ECONNREFUSED 127.0.0.1:8123
```

**Solution:**
```bash
# Check ClickHouse is running
docker ps | grep clickhouse

# If not running
docker-compose up -d clickhouse

# Test connection
curl http://localhost:8123/ping
# Should return: "Ok."

# Check logs
docker-compose logs clickhouse
```

#### Deserialization Errors

**Symptoms:**
```
❌ Error parsing instruction: Invalid Borsh data
```

**Causes:**
1. Program updated event schema (rare)
2. Discriminator mismatch
3. Incorrect field order

**Debug:**
```typescript
// Add logging in parser
console.log('Instruction data (hex):', data.toString('hex'));
console.log('Discriminator:', data.subarray(0, 16).toString('hex'));

// Compare with known discriminators
// Jupiter: e445a52e51cb9a1d40c6cde8260871e2
// Pump: e445a52e51cb9a1dbddb7fd34ee661ee
```

#### Slow Processing

**Symptoms:** < 10 blocks/second

**Solutions:**

1. **Increase Batch Size:**
```bash
export SOLANA_BATCH_SIZE=500
```

2. **Check RPC Rate Limit:**
```bash
# Use paid RPC
export SOLANA_RPC_URL=https://rpc.helius.xyz/?api-key=KEY
export SOLANA_RPC_RATE_LIMIT=100
```

3. **Monitor ClickHouse:**
```sql
-- Check query performance
SELECT 
    query,
    elapsed,
    read_rows,
    memory_usage
FROM system.query_log
WHERE type = 'QueryFinish'
ORDER BY event_time DESC
LIMIT 10;
```

4. **Optimize Whitelist:**
```bash
# Smaller whitelist = faster filtering
wc -l whitelist.txt  # Check size
```

#### Memory Issues

**Symptoms:**
- Indexer crashes with "JavaScript heap out of memory"
- Docker container OOM killed

**Solutions:**

1. **Increase Node.js Memory:**
```bash
# In package.json scripts
"start:solana": "node --max-old-space-size=4096 lib/main-solana.js"
```

2. **Reduce Batch Size:**
```bash
export SOLANA_BATCH_SIZE=50
```

3. **Docker Resource Limits:**
```yaml
# docker-compose.yaml
services:
  indexer:
    deploy:
      resources:
        limits:
          memory: 4G
        reservations:
          memory: 2G
```

---

## Performance

### Benchmarks

**Typical Performance (default settings):**
- **Blocks/sec**: 50-150 blocks/sec
- **Trades/sec**: 10-100 trades/sec (varies by block content)
- **Memory Usage**: 500MB - 2GB
- **CPU Usage**: 1-2 cores

**Optimized Performance:**
- **Blocks/sec**: 200-500 blocks/sec
- **Batch Size**: 500-1000
- **RPC**: Paid provider (Helius, Alchemy)
- **Memory**: 4GB+

### Optimization Tips

**1. Batch Size Tuning**
```bash
# Start conservative
SOLANA_BATCH_SIZE=100

# Increase if:
# - Memory usage is low (<50%)
# - Processing speed plateaus
SOLANA_BATCH_SIZE=500

# Decrease if:
# - Memory errors occur
# - ClickHouse timeouts
SOLANA_BATCH_SIZE=50
```

**2. RPC Provider**
```bash
# Free (slow, rate limited)
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com

# Paid (fast, high limits) - RECOMMENDED
SOLANA_RPC_URL=https://rpc.helius.xyz/?api-key=YOUR_KEY
SOLANA_RPC_RATE_LIMIT=100
```

**3. ClickHouse Configuration**

Create `clickhouse-config.xml`:
```xml
<clickhouse>
    <max_memory_usage>10000000000</max_memory_usage>
    <max_bytes_before_external_group_by>5000000000</max_bytes_before_external_group_by>
    <max_insert_block_size>1048576</max_insert_block_size>
</clickhouse>
```

**4. Token Whitelist**
```bash
# Smaller whitelist = faster processing
# Only include tokens you need

# Check whitelist size
wc -l whitelist.txt

# Filter top tokens only
head -n 1000 whitelist.txt > whitelist_top1k.txt
mv whitelist_top1k.txt whitelist.txt
```

### Monitoring Queries

**Indexer Progress:**
```sql
SELECT 
    state_value as last_height,
    toDateTime(updated_at) as last_update,
    now() - toDateTime(updated_at) as seconds_behind
FROM solana_indexer.solana_indexer_state FINAL
WHERE state_key = 'last_processed_block';
```

**Trade Volume (Last 24h):**
```sql
SELECT 
    amm,
    COUNT(*) as trades,
    SUM(amount_native) as sol_volume,
    COUNT(DISTINCT wallet_address) as unique_wallets
FROM solana_indexer.dex_trades
WHERE block_timestamp > toUnixTimestamp(now() - INTERVAL 1 DAY)
GROUP BY amm;
```

**Database Size:**
```sql
SELECT 
    table,
    formatReadableSize(sum(bytes)) as size,
    sum(rows) as rows
FROM system.parts
WHERE database = 'solana_indexer'
  AND active
GROUP BY table;
```

**Processing Rate:**
```sql
SELECT 
    toStartOfHour(toDateTime(block_timestamp)) as hour,
    COUNT(*) as trades_per_hour
FROM solana_indexer.dex_trades
WHERE block_timestamp > toUnixTimestamp(now() - INTERVAL 24 HOUR)
GROUP BY hour
ORDER BY hour DESC;
```

---

## FAQ

**Q: What's the difference between slot and height?**  
A: Slots are Solana's native block numbers. Heights are Subsquid's internal indexing numbers (height ≈ slot - 22M). Always use heights in config.

**Q: Can I run multiple indexers simultaneously?**  
A: Yes! Configure different `CHAIN_ID` values and different ClickHouse databases. Or use the same database with different state chains.

**Q: How do I resume after stopping the indexer?**  
A: The state is automatically saved in `solana_indexer_state` table. Just restart - it will resume from the last processed block.

**Q: What if I want to re-index from scratch?**  
A: Delete state and data:
```sql
-- Clear state
TRUNCATE TABLE solana_indexer.solana_indexer_state;

-- Clear trades
TRUNCATE TABLE solana_indexer.dex_trades;
```

**Q: Why am I getting fewer trades than expected?**  
A: Check your whitelist. If enabled, only trades with whitelisted tokens are indexed. Empty `whitelist.txt` to index all trades.

**Q: Is this safe for production?**  
A: Yes! The indexer includes:
- Automatic state checkpointing
- Error recovery
- Graceful shutdown
- Battle-tested Subsquid framework

**Q: Can I customize the trade schema?**  
A: Yes! Modify the parser functions to extract additional fields, then update the ClickHouse schema via Alembic migration.

**Q: Does this support other Solana DEXes?**  
A: Not yet, but it's easy to add! Follow the [Adding New DEX Protocols](#adding-new-dex-protocols) guide.

---

## License

MIT

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch
3. Add tests for new functionality
4. Submit pull request with clear description

---

## Support

For issues and questions:
- Create GitHub issue
- Check [Subsquid Discord](https://discord.gg/subsquid)
- Review Subsquid [documentation](https://docs.subsquid.io/)

---

**Built with ❤️ using Subsquid SDK**
