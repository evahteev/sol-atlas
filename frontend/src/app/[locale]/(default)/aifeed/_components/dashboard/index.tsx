'use client'

import clsx from 'clsx'

import Dashboard from '@/components/composed/Dashboard'
import { useQueryResponse } from '@/hooks/warehouse/useQueryResponse'
import { TWarehouseQueryResponse } from '@/services/warehouse-redash/types'
import { getDate } from '@/utils/dates'

import styles from './dashboard.module.scss'

type DashboardTranslations = {
  totalUsers: string
  actions: string
  actionsUnit: string
  actionsPrevious: string
  dailyActiveUsers: string
  dau: string
  caps: string
  usersDynamics: string
  actionsDynamics: string
  capsDynamics: string
}

export const PageCommunityDashboard = ({
  className,
  initialData,
  translations,
}: {
  className?: string
  initialData?: TWarehouseQueryResponse
  translations: DashboardTranslations
}) => {
  const t = (key: keyof DashboardTranslations) => translations[key]

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
          caption: t('totalUsers'),
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
          caption: t('actions'),
          suffix: t('actionsUnit'),
          value: (data?.actions_24h as number) ?? null,
          isLoading,
          delta: {
            value: (data?.actions_percent_change_today as number) ?? null,
            unit: t('actionsPrevious'),
          },
        },
        {
          type: 'counter',
          className: styles.counter,
          caption: t('dailyActiveUsers'),
          suffix: t('dau'),
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
          caption: t('caps'),
          value: (data?.caps_24h as number) ?? null,
          isLoading,
          delta: {
            value: (data?.caps_percent_change_today as number) ?? null,
            unit: '%',
          },
        },
        {
          type: 'chart',
          caption: t('usersDynamics'),
          className: styles.chart,
          isLoading,
          data: (
            JSON.parse(`${data?.users_dynamics || '[]'}`) as { date: string; value: number }[]
          )?.map((item) => ({ x: getDate(item.date), y: item.value })),
          color: '#6046FF',
        },
        {
          type: 'chart',
          caption: t('actionsDynamics'),
          isLoading,
          className: styles.chart,
          data: (
            JSON.parse(`${data?.actions_dynamics || '[]'}`) as { date: string; value: number }[]
          )?.map((item) => ({ x: getDate(item.date), y: item.value })),
          color: '#00E2FB',
        },
        {
          type: 'chart',
          caption: t('capsDynamics'),
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
