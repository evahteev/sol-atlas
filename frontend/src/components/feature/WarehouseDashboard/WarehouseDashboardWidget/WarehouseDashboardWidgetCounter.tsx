import { FC, ReactNode } from 'react'

import clsx from 'clsx'

import { formatAutoDetect } from '@/utils/format'

import styles from './WarehouseDashboardWidget.module.scss'

type WarehouseDashboardWidgetCounterProps = {
  isLoading?: boolean
  value?: string | number | null
  unit?: ReactNode
  subtitle?: ReactNode
}

export const WarehouseDashboardWidgetCounter: FC<WarehouseDashboardWidgetCounterProps> = ({
  value,
  unit,
  subtitle,
  isLoading,
}) => {
  return (
    <div className={styles.counter}>
      <span className={clsx(styles.counterValue, { [styles.loading]: isLoading })}>
        {value || value === 0 ? (
          formatAutoDetect(value)
        ) : (
          <span className={styles.counterUnit}>&mdash;</span>
        )}
        {!!unit && <span className={styles.counterUnit}>{unit}</span>}
      </span>{' '}
      <span className={styles.counterTitle}>{subtitle || <>&nbsp;</>}</span>
    </div>
  )
}
