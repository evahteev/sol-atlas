'use client'

import clsx from 'clsx'

import Dashboard from '@/components/composed/Dashboard'
import { useQueryResponse } from '@/hooks/warehouse/useQueryResponse'
import { TWarehouseQueryResponse } from '@/services/warehouse-redash/types'
import { getDate } from '@/utils/dates'

import styles from './dashboard.module.scss'

export const PageCommunityDashboard = ({
  className,
  initialData,
}: {
  className?: string
  initialData?: TWarehouseQueryResponse
}) => {
  const { result } = useQueryResponse({
    queryId: 'admin_panel_combined',
    maxAge: 0,
    refetchInterval: 5 * 60 * 1000,
    initialData,
  })

  const data = result?.data?.rows[0] ?? null
  const isLoading = data === null

  return (
    <Dashboard
      className={clsx(styles.dashboard, className)}
      widgets={[
        {
          type: 'counter',
          className: styles.counter,
          caption: 'Users Total',
          value: (data?.users_total as number) ?? null,
          isLoading,
          delta: [
            { value: (data?.new_users_24h as number) ?? null, suffix: ' 24h' },
            { value: (data?.new_users_30d as number) ?? null, suffix: ' 30d' },
          ],
        },
        {
          type: 'counter',
          className: styles.counter,
          caption: 'Actions',
          suffix: '24H',
          value: (data?.actions_24h as number) ?? null,
          isLoading,
          delta: {
            value: (data?.actions_percent_change_today as number) ?? null,
            unit: '% vs previous 24h',
          },
        },
        {
          type: 'counter',
          className: styles.counter,
          caption: 'Daily Active Users',
          suffix: 'DAU',
          value: (data?.dau_24h as number) ?? null,
          isLoading,
          delta: {
            value: (data?.dau_percent_change_today as number) ?? null,
            unit: '%',
          },
        },
        {
          type: 'counter',
          className: styles.counter,
          caption: 'CAPS',
          value: (data?.caps_24h as number) ?? null,
          isLoading,
          delta: {
            value: (data?.caps_percent_change_today as number) ?? null,
            unit: '%',
          },
        },
        {
          type: 'chart',
          caption: 'Users Total Dynamics',
          className: styles.chart,
          isLoading,
          data: (
            JSON.parse(`${data?.users_dynamics || '[]'}`) as { date: string; value: number }[]
          )?.map((item) => ({ x: getDate(item.date), y: item.value })),
          color: '#6046FF',
        },
        {
          type: 'chart',
          caption: 'Actions Total Dynamics',
          isLoading,
          className: styles.chart,
          data: (
            JSON.parse(`${data?.actions_dynamics || '[]'}`) as { date: string; value: number }[]
          )?.map((item) => ({ x: getDate(item.date), y: item.value })),
          color: '#00E2FB',
        },
        {
          type: 'chart',
          caption: 'Community Activity Points',
          className: styles.chart,
          isLoading,
          data: (
            JSON.parse(`${data?.caps_dynamics || '[]'}`) as { date: string; value: number }[]
          )?.map((item) => ({ x: getDate(item.date), y: item.value })),
          color: '#FB7900',
        },
      ]}
    />
  )
}
