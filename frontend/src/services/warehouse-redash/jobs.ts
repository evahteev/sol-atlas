import { TWarehouseJob } from './types'
import { warehouseFetch } from './utils'

export async function fetchWarehouseJob(id: string) {
  return warehouseFetch({
    url: `/jobs/${id}`,
    next: { revalidate: 5, tags: ['add', 'fetch', 'fetchWarehouseJob'] },
  })
}
export async function getWarehouseJob(id: string): Promise<TWarehouseJob | null> {
  return fetchWarehouseJob(id)
    .then((res) => res.json())
    .catch(() => {
      return null
    })
}
