'use client'

import { FC } from 'react'

import Loader from '@/components/atoms/Loader'
import StateMessage from '@/components/composed/StateMessage'
import { useDashboard } from '@/hooks/warehouse/useDashboard'

import { WarehouseDashboard, WarehouseDashboardProps } from '../WarehouseDashboard'

import styles from '../WarehouseDashboard.module.scss'

export const WarehouseDashboardBySlugClient: FC<
  Omit<WarehouseDashboardProps, 'dashboard'> & { slug: string | number }
> = ({ slug, params, readOnlyParams, allowUpdate, showTitle = true }) => {
  const { data: dashboard, isLoading } = useDashboard(slug)

  if (isLoading) {
    return <Loader className={styles.loader} />
  }

  if (!dashboard) {
    return <StateMessage type="danger" caption="Dashboard not found" />
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
