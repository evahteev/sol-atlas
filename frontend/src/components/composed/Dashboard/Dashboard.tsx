'use client'

import { DetailedHTMLProps, HTMLAttributes } from 'react'

import clsx from 'clsx'

import { DashboardWidget, DashboardWidgetProps } from './DashboardWidget'

import styles from './Dashboard.module.scss'

export const Dashboard = ({
  className,
  widgets,
}: DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement> & {
  widgets: DashboardWidgetProps[]
}) => {
  return (
    <ul className={clsx(styles.list, className)}>
      {widgets?.map((widget, idx) => {
        return (
          <li className={clsx(styles.item, widget.className)} key={idx}>
            <DashboardWidget {...widget} className={styles.widget} />
          </li>
        )
      })}
    </ul>
  )
}
