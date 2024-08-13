export type TokenModel = {
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

  logoURI: string[]
  symbols: string[]
  marketType: MarketType
  underlyingAddresses?: null | string[]
  tokenListsNames?: string[]
  wallet_category?: Category
  transactionTimestamp?: number
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

export type TokenTag = {
  id: string
  tag_name: string
  short_name: string
  description: string
  logo_uri: string
  tag_type: string
  doc_type: string
}

export type TokenProfilePriceTotals = {
  rank: null
  tags: TokenTag[]
  verifiedTokenListsCount: number
  verifiedTokenListsNames: string[]
  maxSupply: number
  fullyDilutedValuation: number
  fullyDilutedValuationDailyDelta: number
  fullyDilutedValuationInNative: number
  fullyDilutedValuationDailyDeltaInNative: number
  holdersCount: number
}

type ChartData = Array<{
  timestamp: number // 1635811200
  value: number // 920
}>

export type TokenProfileCharts = {
  totalHolders?: number
  totalHoldersDelta?: number
  holdersChart?: ChartData
  transactions24H?: number
  transactions24HDailyDelta?: number
  transactionsChart?: ChartData
  holdersMakingMoney?: {
    at_money: number
    in: number
    out: number
  }
}

export declare enum MarketType {
  lp = 'lp',
  token = 'token',
  account = 'account',
}

export declare enum TraderAdditionalCategoryName {
  liquiditypool = 'liquiditypool',
}

export declare enum LiquidityProviderCategoryName {
  rooster = 'rooster',
  tiger = 'tiger',
  elephant = 'elephant',
}

export declare type Category = TraderAdditionalCategoryName | LiquidityProviderCategoryName

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

export type TokenProfileBalanceKey =
  | '0_10'
  | '10_50'
  | '50_100'
  | '100_250'
  | '250_500'
  | '500_'
  | 'total'
export const TokenProfileBalanceData: Record<string, string> = {
  '0_10': '< $10k',
  '10_50': '$10K–$50K',
  '50_100': '$50k–$100k',
  '100_250': '$100k–$250k',
  '250_500': '$250k–$500k',
  '500_': '$500k+',
  total: 'Total',
}

export type TokenProfileTimeKey = '24' | '1_7' | '7_30' | '30_90' | '90_180' | '180'
export const TokenProfileTimeData: Record<string, string> = {
  '24': '< 24 Hours',
  '1_7': '1-7 Days',
  '7_30': '7-30 Days',
  '30_90': '30-90 Days',
  '90_180': '90-180 Days',
  '180': '180+ Days',
}
