'use client'

import { useQuery } from '@tanstack/react-query'
import { UseQueryParameters } from 'wagmi/query'

import { getWarehouseDashboard } from '@/services/warehouse-redash'
import { TWarehouseDashboard } from '@/services/warehouse-redash/types'

export const useDashboard = (
  id: string | number,
  query?: Partial<UseQueryParameters<TWarehouseDashboard | null>>
) =>
  useQuery<TWarehouseDashboard | null>({
    ...query,
    queryKey: [id],
    queryFn: () => getWarehouseDashboard(id),
  })
