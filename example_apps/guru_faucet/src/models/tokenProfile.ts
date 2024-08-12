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
