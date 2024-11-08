import { FC } from 'react'

import clsx from 'clsx'

import { TWarehouseDashboard } from '@/actions/warehouse/types'
import { getWarehouseDashboardParams } from '@/actions/warehouse/utils'
import { Caption, Show, Tab } from '@/components/ui'

import { WarehouseDashboard } from '../WarehouseDashboard'
import WarehouseDashboardAnalyzerChat from './WarehouseDashboardAnalyzerChat'
import WarehouseDashboardAnalyzerHistoryProvider from './WarehouseDashboardAnalyzerHistoryProvider'
import { WarehouseDashboardAnalyzerOverview } from './WarehouseDashboardAnalyzerOveriew'

import styles from './WarehouseDashboardAnalyzer.module.scss'

export type WarehouseDashboardAnalyzerHistoryEntryProps = {
  prompt_submitted: string
  summary: string
}

export const WarehouseDashboardAnalyzer: FC<{
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
                Guru AI
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
