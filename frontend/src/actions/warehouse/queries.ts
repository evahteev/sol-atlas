'use server'

import { TWarehouseQuery, TWarehouseQueryResponse, TWarehouseQueryResult } from './types'
import { warehouseFetch } from './utils'

export const fetchWarehouseQuery = (id: number) => {
  return warehouseFetch({
    url: `/queries/${id}`,
    next: { revalidate: 60, tags: ['all', 'fetch', 'fetchWarehouseQuery'] },
  })
}
export const getWarehouseQuery = (id: number): Promise<TWarehouseQuery | null> =>
  fetchWarehouseQuery(id)
    .then((res) => res.json())
    .catch(() => null)

export const fetchWarehouseQueryResponse = (
  id: number,
  parameters?: Record<string, unknown>,
  maxAge?: number
) => {
  return warehouseFetch({
    url: `/queries/${id}/results`,
    data: {
      parameters: parameters || {},
      max_age: maxAge,
    },
    next: { revalidate: 5, tags: ['all', 'fetch', 'fetchWarehouseQueryResponse'] },
  })
}
export const getWarehouseQueryResponse = async (
  id: number,
  parameters?: Record<string, unknown>,
  maxAge?: number
): Promise<TWarehouseQueryResponse | null> =>
  fetchWarehouseQueryResponse(id, { ...parameters }, maxAge ?? 24 * 60 * 60)
    .then((res) => res.json())
    .catch(() => {
      return null
    })

export const fetchWarehouseQueryCachedResult = (query_id: number, cached_id?: number) => {
  return warehouseFetch({
    url: `/queries/${query_id}/results/${cached_id}.json`,
    next: { revalidate: 60 * 60, tags: ['add', 'fetch', 'fetchWarehouseQueryCachedResult'] },
  })
}
export const getWarehouseQueryCachedResult = async (
  query_id: number,
  cached_id?: number
): Promise<TWarehouseQueryResult | null> =>
  fetchWarehouseQueryCachedResult(query_id, cached_id)
    .then((res) => res.json())
    .catch(() => {
      return null
    })
