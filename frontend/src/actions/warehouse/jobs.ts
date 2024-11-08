'use server'

import { TWarehouseJob } from './types'
import { warehouseFetch } from './utils'

export const fetchWarehouseJob = (id: string) => {
  return warehouseFetch({
    url: `/job/${id}`,
    next: { revalidate: 5, tags: ['add', 'fetch', 'fetchWarehouseJob'] },
  })
}
export const getWarehouseJob = (id: string): Promise<TWarehouseJob | null> =>
  fetchWarehouseJob(id)
    .then((res) => res.json())
    .catch(() => {
      return null
    })
