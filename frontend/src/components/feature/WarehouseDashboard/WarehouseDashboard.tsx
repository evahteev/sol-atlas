import { FC } from 'react'

import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
import { TWarehouseDashboard, TWarehouseQueryResponse } from '@/services/warehouse-redash/types'
import { getWarehouseDashboardParams } from '@/services/warehouse-redash/utils'

import WarehouseDashboardParams from './WarehouseDashboardParams'
import { WarehouseDashboardWidget } from './WarehouseDashboardWidget/WarehouseDashboardWidget'

import styles from './WarehouseDashboard.module.scss'

export type WarehouseDashboardProps = {
  dashboard: TWarehouseDashboard
  params?: Record<string, string | undefined>
  readOnlyParams?: string[]
  queryResponses?: Record<number, TWarehouseQueryResponse>
  showTitle?: boolean
  allowUpdate?: boolean
}

export const WarehouseDashboard: FC<WarehouseDashboardProps> = ({
  dashboard,
  params,
  readOnlyParams,
  showTitle = true,
  allowUpdate = true,
}) => {
  const { name, widgets } = dashboard

  const sortedWidgets =
    widgets
      ?.filter((widget) => !widget.options.isHidden)
      .sort((a, b) => {
        const aPos = a.options.position.row * 100 + a.options.position.col
        const bPos = b.options.position.row * 100 + b.options.position.col

        return aPos - bPos
      }) || []

  const parameters = getWarehouseDashboardParams(dashboard, params)

  return (
    <>
      <Show if={showTitle}>
        <Caption variant="header" size="lg">
          {name}
        </Caption>
      </Show>
      {dashboard.dashboard_filters_enabled && sortedWidgets.length && (
        <div className={styles.header}>
          <WarehouseDashboardParams
            className={styles.parameters}
            dashboard={dashboard}
            params={parameters}
            readOnlyParams={readOnlyParams}
          />
        </div>
      )}
      <div className={styles.body}>
        {sortedWidgets.map((widget) => (
          <WarehouseDashboardWidget
            widget={widget}
            key={widget.id}
            params={parameters}
            allowUpdate={allowUpdate}
          />
        ))}
      </div>
    </>
  )
}
