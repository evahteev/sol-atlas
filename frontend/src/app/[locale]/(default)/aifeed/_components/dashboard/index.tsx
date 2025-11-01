'use client'

import { useEffect, useState } from 'react'

import clsx from 'clsx'

import Dashboard from '@/components/composed/Dashboard'
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

  // Use initial data immediately
  const initialRowData = initialData?.query_result?.data?.rows[0] ?? null
  const [data, setData] = useState(initialRowData)
  const [isLoading, setIsLoading] = useState(data === null)

  // Set up periodic data fetching on the client side
  useEffect(() => {
    if (typeof window === 'undefined' || !initialData) return

    const fetchData = async () => {
      try {
        const response = await fetch('/api/warehouse-redash', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            queryId: 'admin_panel_combined',
            params: {},
            maxAge: 0,
          }),
        })

        if (response.ok) {
          const result: TWarehouseQueryResponse = await response.json()
          const newData = result?.query_result?.data?.rows[0] ?? null
          if (newData) {
            setData(newData)
            setIsLoading(false)
          }
        }
      } catch (error) {
        console.warn('Failed to fetch updated dashboard data:', error)
      }
    }

    // Set up interval for periodic updates (5 minutes)
    const interval = setInterval(fetchData, 5 * 60 * 1000)

    return () => clearInterval(interval)
  }, [initialData])

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
