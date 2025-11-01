'use server'

import { FC } from 'react'

import StateMessage from '@/components/composed/StateMessage'
import { getWarehouseDashboard } from '@/services/warehouse-redash'

import { WarehouseDashboard, WarehouseDashboardProps } from '../WarehouseDashboard'

export const WarehouseDashboardBySlugServer: FC<
  Omit<WarehouseDashboardProps, 'dashboard'> & { slug: string | number }
> = async ({ slug, params, readOnlyParams, allowUpdate, showTitle = true }) => {
  const dashboard = await getWarehouseDashboard(slug)

  if (!dashboard) {
    return <StateMessage type="danger" caption="No dashboard found" />
  }

  return (
    <WarehouseDashboard
      dashboard={dashboard}
      params={params}
      readOnlyParams={readOnlyParams}
      showTitle={showTitle}
      allowUpdate={allowUpdate}
    />
  )
}
