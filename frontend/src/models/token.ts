export declare enum TokenTraderAdditionalCategoryName {
  liquiditypool = 'liquiditypool',
}

export declare enum TokenLiquidityProviderCategoryName {
  rooster = 'rooster',
  tiger = 'tiger',
  elephant = 'elephant',
}

export declare type TokenCategory =
  | TokenTraderAdditionalCategoryName
  | TokenLiquidityProviderCategoryName
export declare enum TokenMarketType {
  lp = 'lp',
  token = 'token',
  account = 'account',
}

export type TokenCommonModel = {
  address: string
  id: string
  network: string
  name: string
  AMM: string
  blockNumber: number
  decimals: number
  description: string
  liquidityETH: number
  liquidityETHChange24h: number
  liquidityUSD: number
  liquidityUSDChange24h: number
  priceETH: number
  priceETHChange24h: number
  priceUSD: number
  priceUSDChange24h: number
  txns24h: number
  txns24hChange: number
  verified: boolean
  timestamp: number
  volume24h: number
  volume24hETH: number
  volume24hUSD: number
  volumeETHChange24h: number
  volumeUSDChange24h: number
  marketCap?: number
  marketCapChange24h?: number

  marketType: TokenMarketType
  underlyingAddresses?: null | string[]
  tokenListsNames?: string[]
  wallet_category?: TokenCategory
  transactionTimestamp?: number
}

export type TokenV3Model = TokenCommonModel & {
  logoURI: string[]
  symbols: string[]
}

export type TokenV2Model = TokenCommonModel & { logoURI: string; symbol: string }

export type TokenTagModel = {
  id: string
  tag_name: string
  short_name: string
  description: string
  logo_uri?: string
  tag_type: string
}

export type TokenProfile = {
  id: string
  symbol: string
  network: string
  logo_uri: string | null
  token_address: string
  heavy_traders_cot: number
  current: {
    price_usd: number
    volume_usd: number
    price_eth: number
    volume_eth: number
  }
  trending: {
    day: {
      price_move: number
      volume_move: number
    }
    week: {
      price_move: number
      volume_move: number
    }
    month: {
      price_move: number
      volume_move: number
    }
    year: {
      price_move: number
      volume_move: number
    }
  }
  holders_count: number
  fully_diluted_valuation: number
  fully_diluted_valuation_daily_delta: number
  token_supply: number
  liquidity_usd: number
  liquidity_usd_change24h: number
  txns24h: number
  txns24h_change: number
  price_usd_max: number
  price_usd_max_delta: number
  holdersMakingMoney: {
    in: number
    at_money: number
    out: number
  }
  chart: { timestamp: number; price: number; volume: number }[]
}

export type TokenProfileHistory = {
  id: string
  dailyTxns: number
  date: number
  currency: string
  dailyVolume: number
  totalLiquidity: number
  AMM: string
  network: string
  price: number
}

export type TokenProfilePriceStatistics = {
  current_price: number
  hour_ago_price: number
  hour_ago_price_delta: number
  day_ago_price: number
  day_ago_price_delta: number
  week_ago_price: number
  week_ago_price_delta: number
  year_to_date_price: number
  year_to_date_price_delta: number
  max_price: number
  max_price_delta: number
}

export type TokenProfilePriceTotals = {
  rank: null
  tags: TokenTagModel[]
  verifiedTokenListsCount: number
  verifiedTokenListsNames: string[]
  maxSupply: number
  fullyDilutedValuation: number
  fullyDilutedValuationDailyDelta: number
  fullyDilutedValuationInNative: number
  fullyDilutedValuationDailyDeltaInNative: number
  holdersCount: number
}

type TokenProfileChartData = Array<{
  timestamp: number // 1635811200
  value: number // 920
}>

export type TokenProfileCharts = {
  totalHolders?: number
  totalHoldersDelta?: number
  holdersChart?: TokenProfileChartData
  transactions24H?: number
  transactions24HDailyDelta?: number
  transactionsChart?: TokenProfileChartData
  holdersMakingMoney?: {
    at_money: number
    in: number
    out: number
  }
}

export type TrendingToken = {
  id: string
  network: string
  symbol: string
  tokenAddress: string
  heavyTradersCOT: number
  logoURI: string[]
  symbols: string[]
  current: {
    priceUSD: number
    volumeUSD: number
    priceETH: number
    volumeETH: number
  }
  trending: {
    day: {
      priceMove: number
      volumeMove: number
    }
    week: {
      priceMove: number
      volumeMove: number
    }
    month: {
      priceMove: number
      volumeMove: number
    }
  }
  chart: {
    volume: number
    price: number
    timestamp: number
  }[]
}

export type WalletTokenBalance = {
  balance: number // 0.074577
  chain_id: string // '8453'
  token_address: string // '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913'
  token_symbol: string // 'USDC'
}

export type TokenV3ModelWithBalances = TokenV3Model & WalletTokenBalance

export type WalletTotals = {
  balances: TokenV3ModelWithBalances[]
}
