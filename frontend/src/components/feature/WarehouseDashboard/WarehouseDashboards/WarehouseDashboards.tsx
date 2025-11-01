import { FC, HTMLAttributes } from 'react'

import clsx from 'clsx'

import StateMessage from '@/components/composed/StateMessage'
import { TWarehouseDashboard } from '@/services/warehouse-redash/types'

import { WarehouseDashboardsList } from './WarehouseDashboardsList/WarehouseDashboardsList'

import styles from './WarehouseDashboards.module.scss'

type WarehouseDashboardsProps = HTMLAttributes<HTMLDivElement> & {
  dashboards: TWarehouseDashboard[] | null
  tag?: string
  slug?: string
}

export const WarehouseDashboards: FC<WarehouseDashboardsProps> = async ({
  dashboards = [],
  tag,
  slug,
  className,
  children,
  prefix,
  ...props
}) => {
  if (!tag || !dashboards?.length) {
    return (
      <StateMessage type="danger" className={styles.error} caption="No active dashboards found" />
    )
  }

  return (
    <div className={clsx(styles.container, className)} {...props}>
      <div className={styles.header}>
        <WarehouseDashboardsList prefix={prefix} dashboards={dashboards} slug={slug} />
      </div>
      <div className={styles.body}>{children}</div>
    </div>
  )
}
