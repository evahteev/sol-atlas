import { FC } from 'react'

import clsx from 'clsx'
import { env } from 'next-runtime-env'

import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
import Tab from '@/components/ui/Tab'
import { TWarehouseDashboard } from '@/services/warehouse-redash/types'
import { getWarehouseDashboardParams } from '@/services/warehouse-redash/utils'

import { WarehouseDashboard } from '../WarehouseDashboard'
import WarehouseDashboardAnalyzerChat from './WarehouseDashboardAnalyzerChat'
import WarehouseDashboardAnalyzerHistoryProvider from './WarehouseDashboardAnalyzerHistoryProvider'
import { WarehouseDashboardAnalyzerOverview } from './WarehouseDashboardAnalyzerOveriew'

import styles from './WarehouseDashboardAnalyzer.module.scss'

const WarehouseDashboardAnalyzer: FC<{
  className?: string
  dashboard: TWarehouseDashboard
  params?: Record<string, string | undefined>
  readOnlyParams?: string[]
  view?: string
  showTitle?: boolean
}> = ({ className, dashboard, params, readOnlyParams, view, showTitle = true }) => {
  const dashboardParams = getWarehouseDashboardParams(dashboard, params, true)
  const requestParams = Object.fromEntries(
    Object.entries(dashboardParams).map(([key, data]) => [key, data.value])
  )

  return (
    <>
      <Show if={showTitle}>
        <Caption variant="header" size="lg">
          {dashboard.name}
        </Caption>
      </Show>
      <WarehouseDashboardAnalyzerHistoryProvider>
        <div className={clsx(styles.container, className)}>
          <div className={styles.header}>
            <div className={styles.tabs}>
              <Tab href="?" isActive={view !== 'chat'}>
                Dashboard
              </Tab>
              <Tab href="?view=chat" isActive={view === 'chat'}>
                {env('NEXT_PUBLIC_AI_NAME')}
              </Tab>
            </div>
          </div>
          <div className={styles.body}>
            <Show if={view !== 'chat'}>
              <WarehouseDashboardAnalyzerOverview
                slug={dashboard.slug}
                params={requestParams}
                className={styles.overview}
              />

              <WarehouseDashboard
                dashboard={dashboard}
                params={params}
                readOnlyParams={readOnlyParams}
                showTitle={false}
              />
            </Show>

            <Show if={view === 'chat'}>
              <WarehouseDashboardAnalyzerChat
                slug={dashboard.slug}
                params={requestParams}
                className={styles.chat}
              />
            </Show>
          </div>
        </div>
      </WarehouseDashboardAnalyzerHistoryProvider>
    </>
  )
}

export default WarehouseDashboardAnalyzer
