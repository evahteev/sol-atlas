'use server'

import { format } from 'url'

import { TokenModel } from '@/models/token'

export const fetchTokens = async (
  params: {
    ids?: string[]
    network?: string
    sort_by?: string
    order?: string
    field?: string
    value?: string
    from_num?: number
    limit?: number
  } & Record<string, unknown> = {}
): Promise<TokenModel[] | null> =>
  fetch(`${process.env.NEXT_PUBLIC_API_HOST}/v3/tokens`, {
    method: 'POST',
    body: JSON.stringify(params),
  })
    .then((res) => res.json())
    .then((res) => res.data ?? [])
    .catch(() => null)

export const fetchTokensDefault = (network: string, limit = 20): Promise<TokenModel[] | null> =>
  fetchTokens({
    network,
    sort_by: 'volume24hUSD',
    order: 'desc',
    field: 'verified',
    value: 'true',
    from_num: 0,
    limit,
  })

export const fetchTokensSearch = ({
  query,
  ...props
}: {
  query: string
  network?: string
  sort_by?: string
  order?: 'asc' | 'desc'
  include_native?: boolean
}): Promise<TokenModel[] | null> =>
  fetch(
    format({
      pathname: `${process.env.NEXT_PUBLIC_API_HOST}/v3/tokens/search/${query}`,
      query: props,
    }),
    {
      method: 'GET',
    }
  )
    .then((res) => res.json())
    .then((res) => res.data ?? [])
    .catch(() => null)
