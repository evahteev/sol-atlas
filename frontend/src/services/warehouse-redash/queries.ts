import {
  TWarehouseJob,
  TWarehouseQuery,
  TWarehouseQueryResponse,
  TWarehouseQueryResult,
} from './types'
import { warehouseFetch } from './utils'

export async function fetchWarehouseQuery(id: number) {
  return warehouseFetch({
    url: `/queries/${id}`,
    cache: 'no-store',
  })
}
export async function getWarehouseQuery(id: number): Promise<TWarehouseQuery | null> {
  return fetchWarehouseQuery(id)
    .then((res) => {
      if (!res.ok) {
        throw new Error(`Something went wrong in getWarehouseQuery ${id}: ${res.status}`)
      }
      return res.json()
    })
    .catch((e) => {
      console.error(`Catch error in getWarehouseQuery ${id}`, e)
    })
}

export async function fetchWarehouseQueryResponse(
  id: number | string,
  parameters?: Record<string, unknown>,
  maxAge?: number
) {
  return warehouseFetch({
    url: `/queries/${id}/results`,
    data: {
      parameters: parameters || {},
      max_age: maxAge || 0,
    },
    cache: 'no-store',
  })
}
export async function getWarehouseQueryResponse(
  id: number | string,
  parameters?: Record<string, unknown>,
  maxAge?: number
): Promise<TWarehouseQueryResponse | null> {
  return fetchWarehouseQueryResponse(id, { ...parameters }, maxAge ?? 0)
    .then((res) => res.json())
    .catch(() => {
      return null
    })
}

export async function fetchWarehouseJobResponse(id: string) {
  return warehouseFetch({
    url: `/jobs/${id}`,
    cache: 'no-store',
  })
}
export async function getWarehouseJobResponse(id: string): Promise<{ job: TWarehouseJob } | null> {
  return fetchWarehouseJobResponse(id)
    .then((res) => res.json())
    .catch(() => {
      return null
    })
}

export async function fetchWarehouseQueryResult(id: number) {
  return warehouseFetch({
    url: `/query_results/${id}.json`,
    next: { revalidate: 60 * 60 * 24, tags: ['all', 'fetch', 'fetchWarehouseQueryCachedResult'] },
  })
}
export async function getWarehouseQueryResult(
  id: number
): Promise<{ query_result: TWarehouseQueryResult } | null> {
  return fetchWarehouseQueryResult(id)
    .then((res) => res.json())
    .catch(() => {
      return null
    })
}
