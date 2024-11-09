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
  marketType: TokenMarketType
  underlyingAddresses?: null | string[]
  tokenListsNames?: string[]
  wallet_category?: TokenCategory
  transactionTimestamp?: number
}
