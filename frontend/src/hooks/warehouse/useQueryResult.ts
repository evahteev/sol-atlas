'use client'

import { useQuery } from '@tanstack/react-query'
import { UseQueryParameters } from 'wagmi/query'

import { getWarehouseQueryResult } from '@/services/warehouse-redash'
import { TWarehouseQueryResponse } from '@/services/warehouse-redash/types'

export const useQueryResult = (
  id: number,
  query?: Partial<UseQueryParameters<TWarehouseQueryResponse | null>>
) =>
  useQuery<TWarehouseQueryResponse | null>({
    ...query,
    queryKey: [id],
    queryFn: () => getWarehouseQueryResult(id),
  })
