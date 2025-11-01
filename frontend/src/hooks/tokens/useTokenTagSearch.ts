import { useQuery } from '@tanstack/react-query'

import { fetchSearchTokenTags } from '@/actions/tokens'

export const useTokenTagSearch = (query: string) => {
  return useQuery({
    queryKey: [query],
    queryFn: async () => {
      const q = query.trim()

      return q ? fetchSearchTokenTags(query, 100) : []
    },
  })
}
