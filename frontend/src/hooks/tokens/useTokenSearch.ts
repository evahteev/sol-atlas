import { UseQueryOptions, useQuery } from '@tanstack/react-query'

import { fetchTokensDefault, fetchTokensSearch } from '@/actions/tokens'
import { TokenV3Model } from '@/models/token'

export const useTokenSearch = (
  params: Parameters<typeof fetchTokensSearch>[0],
  query?: Partial<UseQueryOptions<TokenV3Model[] | null>>
) => {
  return useQuery({
    ...query,
    queryKey: [params],
    queryFn: async () => {
      const q = params.query.trim()
      return q ? fetchTokensSearch({ ...params, query: q }) : fetchTokensDefault()
    },
  })
}
