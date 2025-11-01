import { FC, ReactNode } from 'react'

import clsx from 'clsx'

import Show from '@/components/ui/Show'

import { DashboardWidgetChart, DashboardWidgetChartProps } from './DashboardWidgetChart'
import { DashboardWidgetCounter, DashboardWidgetCounterProps } from './DashboardWidgetCounter'

import styles from './DashboardWidget.module.scss'

export type DashboardWidgetProps = {
  className?: string
  caption: ReactNode
  suffix?: ReactNode
} & (
  | ({
      type: 'counter'
    } & DashboardWidgetCounterProps)
  | ({ type: 'chart' } & DashboardWidgetChartProps)
)

export const DashboardWidget: FC<DashboardWidgetProps> = (props) => {
  const { caption, suffix, className } = props

  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.header}>
        <strong className={styles.caption}>{caption}</strong>
        <Show if={suffix}>
          {' '}
          <span className={styles.suffix}>{suffix}</span>
        </Show>
      </div>
      <div className={styles.body}>
        {props.type === 'counter' && <DashboardWidgetCounter {...props} />}
        {props.type === 'chart' && <DashboardWidgetChart {...props} />}
      </div>
    </div>
  )
}
