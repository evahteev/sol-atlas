import { useQuery } from '@tanstack/react-query'
import { UseQueryParameters } from 'wagmi/query'

import { fetchTokens } from '@/actions/tokens'
import { TokenV3Model } from '@/models/token'

export const useTokens = (
  params: Parameters<typeof fetchTokens>[0] = {},
  query?: Partial<UseQueryParameters<TokenV3Model[] | null>>
) =>
  useQuery({
    refetchOnWindowFocus: false,
    ...query,
    queryKey: [params],
    queryFn: async () => await fetchTokens(params),
  })
