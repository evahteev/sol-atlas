'use server'

import { isString } from 'lodash'

import { TWarehouseDashboard, TWarehouseDashboardTag } from './types'
import { warehouseFetch } from './utils'

export const fetchWarehouseDashboardTags = () =>
  warehouseFetch({
    url: '/dashboards/tags',
    next: { revalidate: 15 * 60, tags: ['add', 'fetch', 'fetchWarehouseDashboardTags'] },
  })
export const getWarehouseDashboardTags = async (): Promise<TWarehouseDashboardTag[] | null> =>
  (
    await fetchWarehouseDashboardTags()
      .then((res) => res.json())
      .catch((e) => {
        console.log(e)
        return null
      })
  )?.tags ?? null

export const fetchWarehouseDashboards = (tag?: string) =>
  warehouseFetch({
    url: `/dashboards?page_size=100${tag ? `&tags=${tag}` : ''}`,
    next: { revalidate: 10 * 60, tags: ['add', 'fetch', 'fetchWarehouseDashboards'] },
  })
export const getWarehouseDashboards = async (tag?: string): Promise<TWarehouseDashboard[] | null> =>
  (
    await fetchWarehouseDashboards(tag)
      .then((res) => res.json())
      .catch((e) => {
        console.log(e)
        return null
      })
  )?.results?.filter((item: TWarehouseDashboard) => !item.is_draft && !item.is_archived) ?? null

export const fetchWarehouseDashboard = (id: string | number) => {
  return warehouseFetch({
    url: `/dashboards/${id}${isString(id) ? '?legacy=true' : ''}`,
    next: { revalidate: 10 * 60, tags: ['add', 'fetch', 'fetchWarehouseDashboard'] },
  })
}
export const getWarehouseDashboard = async (
  id: string | number
): Promise<TWarehouseDashboard | null> => {
  const dashboard = await fetchWarehouseDashboard(id)
    .then((res) => res.json())
    .catch(() => null)

  if (!dashboard?.is_draft && !dashboard?.is_archived) {
    return dashboard
  }

  return null
}
