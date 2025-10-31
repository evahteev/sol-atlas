'use client'

import { DetailedHTMLProps, HTMLAttributes } from 'react'

import clsx from 'clsx'

import Dashboard from '@/components/composed/Dashboard'
import { useQueryResponse } from '@/hooks/warehouse/useQueryResponse'
import { TWarehouseQueryResponse } from '@/services/warehouse-redash/types'

import styles from './stats.module.scss'

export const PageLauncherDashboardStats = ({
  className,
  initialData,
}: DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement> & {
  initialData?: TWarehouseQueryResponse
}) => {
  const { result } = useQueryResponse({
    queryId: 'guru_network_ecosystem_overview',
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
          caption: 'Total Members',
          value: (data?.total_members as number) ?? null,
          isLoading,
          delta: { value: (data?.total_members_delta as number) ?? null, suffix: ' 24h' },
        },
        {
          type: 'counter',
          caption: 'Total CAPS',
          suffix: '24h',
          value: (data?.total_caps_24h as number) ?? null,
          isLoading,
          delta: { value: (data?.total_caps_24h_delta as number) ?? null, unit: '%' },
        },
        {
          type: 'counter',
          caption: 'Total Actions',
          suffix: '24h',
          value: (data?.total_actions_24h as number) ?? null,
          isLoading,
          delta: { value: (data?.total_actions_24h_delta as number) ?? null, unit: '%' },
        },
        {
          type: 'counter',
          caption: 'AIGURU distributed',
          suffix: '24h',
          value: (data?.aiguru_distributed_24h as number) ?? null,
          isLoading,
          delta: { value: (data?.aiguru_distributed_24h_delta as number) ?? null, unit: '%' },
        },

        {
          type: 'counter',
          caption: 'Active Communities',
          value: (data?.active_communities as number) ?? null,
          isLoading,
          delta: { value: (data?.active_communities_delta as number) ?? null, unit: ' New' },
        },
        {
          type: 'counter',
          caption: 'Guru Chest Grants',
          value: (data?.guru_chest_grants as number) ?? null,
          isLoading,
          delta: { value: (data?.guru_chest_grants_delta as number) ?? null, unit: ' distributed' },
        },
      ]}
    />
  )
}
