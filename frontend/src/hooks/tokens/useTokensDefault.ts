import { UseQueryOptions, useQuery } from '@tanstack/react-query'

import { fetchTokensDefault } from '@/actions/tokens'
import { TokenV3Model } from '@/models/token'

export const useTokensDefault = (
  params: Parameters<typeof fetchTokensDefault>[0],
  query?: Partial<UseQueryOptions<TokenV3Model[] | null>>
) =>
  useQuery({
    refetchOnWindowFocus: false,
    ...query,
    queryKey: [params],
    queryFn: async () => {
      return fetchTokensDefault(params)
    },
  })
