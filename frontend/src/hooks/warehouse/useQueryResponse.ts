'use client'

import { RefetchOptions, keepPreviousData, useQuery } from '@tanstack/react-query'
import { UseQueryParameters } from 'wagmi/query'

import { getWarehouseQueryResponse } from '@/services/warehouse-redash'
import { getWarehouseJobResponse } from '@/services/warehouse-redash/queries'
import {
  TWarehouseJob,
  TWarehouseQueryResponse,
  TWarehouseQueryResult,
} from '@/services/warehouse-redash/types'

import { useQueryResult } from './useQueryResult'

const QUERY_JOB_INTERVAL = 5000

const getIsActiveJob = (job?: TWarehouseJob | null) => {
  return (job?.status || 6) < 3
}

export const useQueryResponse = ({
  queryId,
  initialData,
  params = {},
  maxAge,
  enabled = true,
  refetchInterval,
  query,
}: {
  queryId: number | string
  initialData?: TWarehouseQueryResponse
  params?: Record<string, unknown>
  maxAge?: number
  enabled?: boolean
  refetchInterval?: number
  query?: Partial<UseQueryParameters<TWarehouseQueryResponse | null>>
}): {
  isError: boolean
  isFetching: boolean
  isLoading: boolean
  isRefetching: boolean
  isFetched: boolean
  isActiveJob: boolean
  job?: TWarehouseJob
  result?: TWarehouseQueryResult
  refetch: (options?: RefetchOptions) => void
} => {
  const responseQuery = useQuery<TWarehouseQueryResponse | null>({
    initialData: initialData ?? undefined,
    ...query,
    refetchOnWindowFocus: false,
    refetchInterval,
    queryKey: [queryId, params, maxAge],
    queryFn: () => getWarehouseQueryResponse(queryId, params, maxAge),
    enabled,
  })

  // const responseQueryData = responseQuery.data
  const responseQueryDataJob = responseQuery.data?.job
  const responseQueryDataResult = responseQuery.data?.query_result

  const responseJob = useQuery<{ job?: TWarehouseJob } | null>({
    // initialData: responseQueryDataJob ?? initialData?.job ?? undefined,
    refetchOnWindowFocus: false,
    refetchInterval: (query) => {
      return query.state.fetchStatus !== 'fetching' && getIsActiveJob(query.state.data?.job)
        ? QUERY_JOB_INTERVAL
        : false
    },
    queryKey: [responseQueryDataJob?.id],
    queryFn: () => getWarehouseJobResponse(responseQueryDataJob?.id || ''),
    enabled: !responseQueryDataResult && getIsActiveJob(responseQueryDataJob),
  })

  const responseJobData = responseJob.data

  const responseResult = useQueryResult(responseJobData?.job?.query_result_id || 0, {
    // initialData: responseQueryData ?? initialData ?? undefined,
    placeholderData: keepPreviousData,
    refetchOnWindowFocus: false,
    enabled: !!responseJobData?.job?.query_result_id,
  })

  const result =
    responseResult.data?.query_result ??
    responseQuery.data?.query_result ??
    initialData?.query_result

  const isFetching = responseQuery.isFetching || responseJob.isFetching || responseResult.isFetching
  const isActiveJob = getIsActiveJob(responseJobData?.job)

  return {
    job: responseJobData?.job ?? undefined,
    result: result,

    isError: responseQuery.isError || responseJob.isError || responseResult.isError,
    isFetching,
    isFetched: responseQuery.isFetched && responseJob.isFetched && responseResult.isFetched,
    isActiveJob,
    isLoading: isFetching && isActiveJob,

    refetch: responseQuery.refetch,
    isRefetching: responseQuery.isRefetching,
  }
}
