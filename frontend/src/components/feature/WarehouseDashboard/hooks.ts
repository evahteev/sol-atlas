'use client'

import { useQuery } from '@tanstack/react-query'

import { getWarehouseQueryResponse } from '@/actions/warehouse'
import {
  TWarehouseJob,
  TWarehouseQueryResponse,
  TWarehouseQueryResult,
} from '@/actions/warehouse/types'

const QUERY_JOB_INTERVAL = 5000

const getIsActiveJob = (
  data: { query_result?: TWarehouseQueryResult; job?: TWarehouseJob } | null | undefined
) => {
  return data !== null && !data?.query_result && (data?.job?.status || 0) < 3
}

export const useQueryResponse = ({
  queryId,
  queryResponse,
  params = {},
}: {
  queryId: number
  queryResponse?: TWarehouseQueryResponse
  params?: Record<string, unknown>
}): {
  isError: boolean
  isFetching: boolean
  isActiveJob: boolean
  job?: TWarehouseJob
  result?: TWarehouseQueryResult
} => {
  const { isFetching, data } = useQuery<TWarehouseQueryResponse | null>({
    initialData: queryResponse ?? undefined,
    refetchOnWindowFocus: false,
    refetchInterval: (query) => {
      return query.state.fetchStatus !== 'fetching' && getIsActiveJob(query.state.data)
        ? QUERY_JOB_INTERVAL
        : false
    },
    queryKey: [queryId, params],
    queryFn: async () => {
      return await getWarehouseQueryResponse(queryId, params)
    },
  })

  return {
    isError: data === null,
    isFetching,
    isActiveJob: getIsActiveJob(data),
    job: data?.job,
    result: data?.query_result,
  }
}
