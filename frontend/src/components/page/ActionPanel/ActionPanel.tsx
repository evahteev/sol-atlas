import { HTMLAttributes } from 'react'

import clsx from 'clsx'

import styles from './ActionPanel.module.scss'

export function ActionPanel({ children, className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return (
    <div id="action-panel" className={clsx(styles.container, className)} {...props}>
      {children}
    </div>
  )
}
