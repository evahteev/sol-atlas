import Link from 'next/link'

import { FC } from 'react'

import clsx from 'clsx'

import Dropdown from '@/components/composed/Dropdown'
import StateMessage from '@/components/composed/StateMessage'
import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
import { TWarehouseDashboard } from '@/services/warehouse-redash/types'

import styles from './WarehouseDashboardsList.module.scss'

export const WarehouseDashboardsList: FC<{
  dashboards?: TWarehouseDashboard[]
  slug?: string
  prefix?: string
}> = ({ dashboards, slug, prefix }) => {
  if (!dashboards?.length) {
    return (
      <StateMessage type="danger" className={styles.error} caption="No active dashboards found" />
    )
  }

  const currentDashboard = dashboards.find((dashboard) => slug && dashboard.slug === slug)

  const renderList = (className?: string) => (
    <ul className={clsx(styles.list, className)}>
      {dashboards?.map((dashboard) => (
        <li className={styles.item} key={dashboard.slug}>
          <Link
            href={`${prefix || ''}/${dashboard.slug}`}
            className={clsx(styles.link, { [styles.active]: !!slug && slug === dashboard.slug })}>
            {dashboard.name}
          </Link>
        </li>
      ))}
    </ul>
  )

  return (
    <>
      {renderList()}

      <Show if={dashboards.length > 1}>
        <Dropdown
          variant="custom"
          caption={currentDashboard?.name || 'Select dashboard'}
          className={styles.title}>
          {renderList(styles.select)}
        </Dropdown>
      </Show>

      <Show if={dashboards.length === 1}>
        <Caption variant="header" size="lg" className={styles.title}>
          {dashboards[0].name}
        </Caption>
      </Show>
    </>
  )
}
