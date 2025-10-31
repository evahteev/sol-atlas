export type CoingeckoLinks = {
  homepage: string[]
  whitepaper: string | null
  blockchain_site: string[]
  official_forum_url: string[]
  chat_url: string[]
  announcement_url: string[]
  twitter_screen_name: string | null
  facebook_username: string | null
  bitcointalk_thread_identifier: null
  telegram_channel_identifier: string | null
  subreddit_url: string | null
  repos_url: Record<string, string[]>
}

export type TokenCoingeckoData = {
  links: CoingeckoLinks
  market_cap_rank: number
  market_data: {
    market_cap_rank: number
    market_cap: {
      usd: number
    }
    total_supply: number
    circulating_supply: number
    fully_diluted_valuation: {
      usd: number
    }
  }
}

export const coingeckoApiPlatformIds: Record<string, string> = {
  eth: 'ethereum',
  bsc: 'binance-smart-chain',
  polygon: 'polygon-pos',
  avalanche: 'avalanche',
  arbitrum: 'arbitrum-one',
  fantom: 'fantom',
  celo: 'celo',
}
