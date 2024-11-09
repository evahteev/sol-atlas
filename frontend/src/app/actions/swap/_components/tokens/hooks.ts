import { useQuery } from '@tanstack/react-query'

import { fetchTokens, fetchTokensDefault, fetchTokensSearch } from '@/actions/tokens'

export const useTokens = (params: Parameters<typeof fetchTokens>[0] = {}) =>
  useQuery({
    refetchOnWindowFocus: false,
    queryKey: [params],
    queryFn: async () => {
      return fetchTokens(params)
    },
  })

export const useTokensDefault = (network: string, limit?: number) =>
  useQuery({
    refetchOnWindowFocus: false,
    queryKey: [network, limit],
    queryFn: async () => {
      return fetchTokensDefault(network, limit)
    },
  })

export const useTokensSearch = (params: Parameters<typeof fetchTokensSearch>[0]) =>
  useQuery({
    refetchOnWindowFocus: false,
    queryKey: [params],
    queryFn: async () => {
      return fetchTokensSearch(params)
    },
  })
