import { UTCDate } from '@date-fns/utc'
import { env } from 'next-runtime-env'
import { format } from 'url'
import { Address, Chain, createPublicClient, erc20Abi, formatEther, formatUnits, http } from 'viem'

import { CustomToken } from '@/components/composed/TaskForm/custom/swapToken/types'
import { NATIVE_TOKEN_ADDRESS } from '@/config/settings'
import { guruTestnet, networks } from '@/config/wagmi'
import { TagsFilter } from '@/framework/utils'
import { ChainModel } from '@/models/chain'
import {
  TokenProfile,
  TokenProfileCharts,
  TokenProfileHistory,
  TokenProfilePriceStatistics,
  TokenProfilePriceTotals,
  TokenTagModel,
  TokenV2Model,
  TokenV3Model,
  TrendingToken,
  WalletTokenBalance,
} from '@/models/token'
import { TokenTxHistoryParams } from '@/models/tx'
import { getAsArray } from '@/utils'
import { getTokenId } from '@/utils/tokens'

const getBaseUrl = () =>
  typeof window === 'undefined' ? 'https://api-prod-lax.dexguru.biz' : 'https://api.dex.guru'

export async function fetchChainList(): Promise<ChainModel[] | null> {
  return fetch(`${getBaseUrl()}/v3/chain`, {
    method: 'GET',
    next: {
      revalidate: 30 * 60,
    },
  })
    .then((res) => res.json())
    .then((res) => res?.data ?? [])
    .catch((e) => {
      console.error(e)
      return []
    })
}

export type TFetchTokensParams = {
  ids?: string[]
  network?: string | string[]
  sort_by?: string
  order?: string
  field?: string
  value?: string
  from_num?: number
  limit?: number
  include_native?: boolean
} & Record<string, unknown>

export async function fetchTokens(params: TFetchTokensParams = {}): Promise<TokenV3Model[] | null> {
  return fetch(`${getBaseUrl()}/v3/tokens`, {
    method: 'POST',
    body: JSON.stringify({
      ...params,
      network: params?.network ? getAsArray(params?.network).join(',') : undefined,
    }),
    next: { revalidate: 60 * 5 },
  })
    .then((res) => res.json())
    .then((res) => res.data ?? [])
    .catch(() => null)
}
export async function fetchTokensDefault({
  network,
  include_native = false,
  limit = 20,
}: {
  network?: string
  include_native?: boolean
  limit?: number
} = {}): Promise<TokenV3Model[] | null> {
  return fetchTokens({
    network,
    sort_by: 'volume24hUSD',
    order: 'desc',
    field: 'verified',
    value: 'true',
    from_num: 0,
    include_native,
    limit,
  })
}

export async function fetchTokensSearch({
  query,
  ...props
}: {
  query: string
  network?: string
  sort_by?: string
  order?: 'asc' | 'desc'
  include_native?: boolean
}): Promise<TokenV3Model[] | null> {
  return fetch(
    format({
      pathname: `${getBaseUrl()}/v3/tokens/search/${query}`,
      query: props,
    }),
    {
      method: 'GET',
      next: { revalidate: 60 * 5 },
    }
  )
    .then((res) => res.json())
    .then((res) => res.data ?? [])
    .catch(() => null)
}

export async function fetchTokenTags(tags?: string[]): Promise<TokenTagModel[] | null> {
  const query: { limit: number; tag_ids?: string } = {
    limit: tags?.length ?? 1000,
    tag_ids: tags?.join(','),
  }

  const tagsFilter = await import(`skins/theme/utils`)
    .then((module) => module.tagsFilter as TagsFilter)
    .catch((e) => {
      console.error(`failed dynamic import from skins/theme/utils:`, e)
      return undefined
    })

  return fetch(
    format({
      pathname: `${getBaseUrl()}/v1/token_tags/tags`,
      query,
    }),
    {
      method: 'GET',
      next: { revalidate: 60 * 60 },
    }
  )
    .then((res) => res.json())
    .then((res) => res.data ?? [])
    .then((tags) => tagsFilter?.(tags) || tags)
    .catch(() => null)
}

export async function fetchSearchTokenTags(
  query: string,
  limit?: number
): Promise<TokenTagModel[] | null> {
  return fetch(
    format({
      pathname: `${getBaseUrl()}/v1/token_tags/search/${query}`,
      query: { limit },
    }),
    {
      method: 'GET',
      next: { revalidate: 60 * 60 },
    }
  )
    .then((res) => res.json())
    .then((res) => res.data ?? [])
    .catch(() => null)
}

export async function fetchTokenProfiles({
  tags,
  limit,
  offset,
}: {
  tags: string[]
  limit: number
  offset: number
}): Promise<TokenProfile[] | null> {
  return fetch(
    format({
      pathname: `${getBaseUrl()}/v2/tokens/profiles`,
      query: {
        tag_ids: (tags || []).join(','),
        limit: limit,
        offset: offset,
      },
    }),
    {
      method: 'GET',
      next: { revalidate: 5 * 60 },
    }
  )
    .then((res) => res.json())
    .then((res) => res?.data ?? [])
    .catch(() => null)
}

export async function fetchTokenProfileHistory(
  address: string,
  network: string,
  days = 7
): Promise<TokenProfileHistory[] | null> {
  const endTimestamp = new UTCDate().setHours(0, 0, 0, 0) / 1000 - 1
  const beginTimestamp = Math.round(endTimestamp - days * 3600 * 24 + 1)

  return fetch(
    format({
      pathname: `${getBaseUrl()}/v3/tokens/${getTokenId({ address, network })}/history`,
      query: {
        begin_timestamp: beginTimestamp,
        end_timestamp: endTimestamp,
        currency: 'USD',
        amms: 'all',
        interval: 60 * 60 * 24,
      },
    }),
    {
      next: {
        revalidate: 60 * 60, // interval is 1D, so 1h is enough
        tags: ['all', 'fetch', 'fetchTokenProfileHistory'],
      },
    }
  )
    .then((res) => res.json())
    .catch(() => null)
    .then((res) => res.data ?? [])
}

export async function fetchTokenProfilePriceCharts(
  address: string,
  network: string
): Promise<TokenProfileCharts | null> {
  return fetch(
    `${getBaseUrl()}/v2/tokens/${address.toLowerCase()}/profile/charts?network=${network.toLowerCase()}`,
    {
      next: {
        revalidate: 30 * 60,
        tags: ['all', 'fetch', 'fetchTokenProfilePriceCharts'],
      },
    }
  )
    .then((res) => res.json())
    .catch(() => null)
}

export async function fetchTokenProfilePriceStatistics(
  address: string,
  network: string,
  isNative?: true
): Promise<TokenProfilePriceStatistics | null> {
  return fetch(
    `${getBaseUrl()}/v2/tokens/${address.toLowerCase()}/price_statistics?network=${network.toLowerCase()}&currency=${isNative ? 'N' : 'S'}`,
    {
      next: {
        revalidate: 30 * 60, // min price change is 1h, so 30min is enough
        tags: ['all', 'fetch', 'fetchTokenProfilePriceStatistics'],
      },
      method: 'GET',
    }
  )
    .then((res) => res.json())
    .catch(() => null)
}

export async function fetchTokenProfilePriceTotals(
  address: string,
  network: string
): Promise<TokenProfilePriceTotals | null> {
  return fetch(
    `${getBaseUrl()}/v2/tokens/${address.toLowerCase()}/profile/total?network=${network.toLowerCase()}`,
    {
      next: {
        revalidate: 60 * 60, // for last 24h, so 1h is enough
        tags: ['all', 'fetch', 'fetchTokenProfilePriceTotals'],
      },
      method: 'GET',
    }
  )
    .then((res) => res.json())
    .catch(() => null)
}

export async function fetchTradingHistory(
  symbol: string,
  resolution: string,
  from: number,
  to: number
): Promise<{
  t: number[]
  o: number[]
  h: number[]
  l: number[]
  c: number[]
  v: number[]
  liq: number[]
}> {
  const query = {
    symbol,
    resolution,
    from: Math.floor(from / 1000),
    to: Math.ceil(to / 1000),
  }

  return fetch(
    format({
      pathname: `${getBaseUrl()}/v1/tradingview/history`,
      query,
    }),
    {
      next: {
        revalidate: 2 * 60, // min candle timeframe is 5min, so we use half of it
        tags: ['all', 'fetch', 'fetchTradingHistory'],
      },
    }
  )
    .then((res) => res.json())
    .catch((e) => {
      console.error('getTradingHistory error: ', e)
      return []
    })
}

export async function fetchFinancialChartSearch(query: string): Promise<
  | {
      symbol: string
      full_name: string
      description: string
      exchange: string
      type: string
      ticker: string
    }[]
  | null
> {
  return fetch(
    format({
      pathname: `${getBaseUrl()}/v1/tradingview/search`,
      query: { query },
    }),
    {
      next: {
        revalidate: 2 * 60, // min candle timeframe is 5min, so we use half of it
        tags: ['all', 'fetch', 'fetchFinancialChartSearch'],
      },
    }
  )
    .then((res) => {
      if (!res.ok) {
        return null
      }
      return res.json()
    })
    .catch(() => null)
}

export async function fetchTokensTrending({
  network = [],
  ids = [],
}: {
  network?: string | string[]
  ids?: string[]
}): Promise<TrendingToken[] | null> {
  return fetch(`${getBaseUrl()}/v2/tokens/trending`, {
    method: 'POST',
    next: { revalidate: 5 * 60 },
    body: JSON.stringify({ ids, network: getAsArray(network).join(',') }),
  })
    .then((res) => res.json())
    .then((res) => res?.data ?? [])
    .catch(() => null)
}

export async function fetchTokensGainers({
  currency = 'USD',
  network = [],
  limit = 20,
  offset = 0,
}: {
  currency?: string
  network?: string[] | string
  limit?: number
  offset?: number
}): Promise<TokenV2Model[] | null> {
  return fetch(
    format({
      pathname: `${getBaseUrl()}/v2/tokens/top/gainers`,
      query: { currency, limit, offset, network: getAsArray(network).join(',') },
    }),
    {
      method: 'GET',
      next: { revalidate: 5 * 60 },
    }
  )
    .then((res) => res.json())
    .then((res) => res?.data ?? [])
    .catch(() => null)
}

export async function fetchTokensLosers({
  currency = 'USD',
  network = [],
  limit = 20,
  offset = 0,
}: {
  currency?: string
  network?: string[] | string
  limit?: number
  offset?: number
}): Promise<TokenV2Model[] | null> {
  return fetch(
    format({
      pathname: `${getBaseUrl()}/v2/tokens/top/losers`,
      query: { currency, limit, offset, network: getAsArray(network).join(',') },
    }),
    {
      method: 'GET',
      next: { revalidate: 5 * 60 },
    }
  )
    .then((res) => res.json())
    .then((res) => res?.data ?? [])
    .catch(() => null)
}

export async function fetchTokensRecent({
  currency = 'USD',
  network = [],
  limit = 20,
  offset = 0,
}: {
  currency?: string
  network?: string[] | string
  limit?: number
  offset?: number
}): Promise<TokenV2Model[] | null> {
  return fetch(
    format({
      pathname: `${getBaseUrl()}/v2/tokens/newly_listed`,
      query: { currency, limit, offset, network: getAsArray(network).join(',') },
    }),
    {
      method: 'GET',
      next: { revalidate: 5 * 60 },
    }
  )
    .then((res) => res.json())
    .then((res) => res?.data ?? [])
    .catch(() => null)
}

export async function fetchTokenTxHistoryLast(
  current_token_id: string,
  params: TokenTxHistoryParams = {}
) {
  return fetch(`${getBaseUrl()}/v3/tokens/transactions/last`, {
    body: JSON.stringify({
      current_token_id,
      sort_by: 'timestamp',
      limit: 50,
      offset: 0,
      order: 'desc',
      with_full_totals: false,
      transaction_types: ['mint', 'burn', 'swap', 'transfer'],
      token_status: 'all',
      ...params,
    }),
    method: 'POST',
    next: { revalidate: 15 },
  })
    .then((res) => res.json())
    .then((res) => res?.data ?? [])
    .catch(() => null)
}

export async function getNativeBalances(
  address: string,
  chainsConfig: ChainModel[]
): Promise<WalletTokenBalance[]> {
  const balances = await Promise.all(
    networks.map(async (chain) => {
      if (chain.id === guruTestnet.id) {
        return
      }
      const nativeToken = chainsConfig.find((x) => x.id === chain.id)?.native_token

      if (!nativeToken?.address) {
        return null
      }
      const publicClient = createPublicClient({
        chain: chain as Chain,
        transport: http(chain.rpcUrls.default.http[0]),
      })
      const balance = await publicClient
        .getBalance({
          address: address as Address,
        })
        .catch((e) => {
          console.error(e)
          return null
        })
      if (!balance) {
        return null
      }
      const balanceAsEther = formatEther(balance)
      const result: WalletTokenBalance = {
        balance: Number(balanceAsEther),
        chain_id: `${chain.id}`,
        token_address: NATIVE_TOKEN_ADDRESS,
        token_symbol: nativeToken?.symbols[0].replace(/^W/i, ''),
      }
      return result
    })
  )
  return balances.filter((x) => !!x)
}

export async function getErc20Balances(
  address: string,
  chainsConfig: ChainModel[],
  erc20Tokens: CustomToken[]
): Promise<WalletTokenBalance[]> {
  const balances = await Promise.all(
    networks.map(async (chain) => {
      if (chain.id === guruTestnet.id) {
        return
      }
      const chainConfig = chainsConfig.find((x) => x.id === chain.id)

      const erc20TokensFromChain = erc20Tokens.filter((x) => x.network === chainConfig?.name)
      if (!erc20TokensFromChain.length) {
        return
      }

      const publicClient = createPublicClient({
        chain: chain as Chain,
        transport: http(chain.rpcUrls.default.http[0]),
      })

      const erc20TokenContracts = erc20TokensFromChain.map((x) => ({
        address: x.address as Address,
        abi: erc20Abi,
        functionName: 'balanceOf',
        args: [address],
      }))

      const callResults = await publicClient
        .multicall({
          contracts: erc20TokenContracts,
        })
        .catch((e) => {
          console.error(e)
          return null
        })
      if (!callResults?.length) {
        return null
      }

      const results: WalletTokenBalance[] = erc20TokensFromChain.map((x, id) => ({
        balance: Number(formatUnits(BigInt(callResults[id]?.result || 0n), x.decimals)),
        chain_id: `${chain.id}`,
        token_address: x.address,
        token_symbol: x.symbols[0],
      }))
      return results
    })
  )
  return balances.flat().filter((x) => !!x)
}
