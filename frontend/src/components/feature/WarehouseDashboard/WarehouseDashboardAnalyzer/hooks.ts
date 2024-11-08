import { useQuery } from '@tanstack/react-query'

import {
  getWarehouseDashboardAnalyze,
  getWarehouseDashboardPrompts,
} from '@/actions/warehouse/analyzer'

import { WarehouseDashboardAnalyzerHistoryEntryProps } from './WarehouseDashboardAnalyzer'

type Params = Record<string, unknown>

export const useDashboardPrompts = (
  slug: string,
  params: Params = {},
  history: WarehouseDashboardAnalyzerHistoryEntryProps[] = [],
  initial: string[] | null
) =>
  useQuery({
    initialData: initial ?? undefined,
    refetchOnWindowFocus: false,
    queryKey: [slug, params, history],
    queryFn: async () => {
      const output = await getWarehouseDashboardPrompts({
        slug,
        params,
        history,
      })

      return output
    },
  })

export const useDashboardAnalyze = ({
  slug,
  params = {},
  prompt = '',
}: {
  slug: string
  params?: Params
  prompt?: string | null
}) =>
  useQuery({
    enabled: !!prompt,
    refetchOnWindowFocus: false,
    queryKey: [slug, params, prompt],
    queryFn: async () => {
      const output = await getWarehouseDashboardAnalyze({
        slug,
        params,
        prompt,
      })

      return output
    },
  })
