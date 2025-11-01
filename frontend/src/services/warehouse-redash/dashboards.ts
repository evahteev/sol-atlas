import isString from 'lodash/isString'

import { TWarehouseDashboard, TWarehouseDashboardTag } from './types'
import { warehouseFetch } from './utils'

export async function fetchWarehouseDashboardTags() {
  return warehouseFetch({
    url: '/dashboards/tags',
    next: { revalidate: 15 * 60, tags: ['add', 'fetch', 'fetchWarehouseDashboardTags'] },
  })
}
export async function getWarehouseDashboardTags(): Promise<TWarehouseDashboardTag[] | null> {
  return (
    (
      await fetchWarehouseDashboardTags()
        .then((res) => res.json())
        .catch((e) => {
          console.log(e)
          return null
        })
    )?.tags ?? null
  )
}

export async function fetchWarehouseDashboards(tag?: string) {
  return warehouseFetch({
    url: `/dashboards?page_size=100${tag ? `&tags=${tag}` : ''}`,
    next: { revalidate: 1 * 60, tags: ['add', 'fetch', 'fetchWarehouseDashboards'] },
  })
}
export async function getWarehouseDashboards(tag?: string): Promise<TWarehouseDashboard[] | null> {
  return (
    (
      await fetchWarehouseDashboards(tag)
        .then((res) => res.json())
        .catch((e) => {
          console.log(e)
          return null
        })
    )?.results?.filter((item: TWarehouseDashboard) => !item.is_draft && !item.is_archived) ?? null
  )
}
export async function fetchWarehouseDashboard(id: string | number) {
  return warehouseFetch({
    url: `/dashboards/${id}${isString(id) ? '?legacy=true' : ''}`,
    next: { revalidate: 1 * 60, tags: ['add', 'fetch', 'fetchWarehouseDashboard'] },
  })
}
export async function getWarehouseDashboard(
  id: string | number
): Promise<TWarehouseDashboard | null> {
  const dashboard = await fetchWarehouseDashboard(id)
    .then(async (res) => {
      if (!res.ok) {
        throw new Error(`Something went wrong in getWarehouseDashboard ${id}: ${res.status}.`)
      }
      return res.json()
    })
    .catch((e) => {
      console.error(`Catch error in getWarehouseDashboard ${id}`, e)
      return null
    })

  return dashboard
  if (!dashboard?.is_draft && !dashboard?.is_archived) {
    return dashboard
  }

  return null
}
