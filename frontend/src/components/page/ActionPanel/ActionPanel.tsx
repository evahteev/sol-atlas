import { HTMLAttributes } from 'react'

import clsx from 'clsx'

import type { DarkColor } from '@/components/ui'

import styles from './ActionPanel.module.scss'

type ActionPanelProps = {
  background?: DarkColor
} & HTMLAttributes<HTMLDivElement>

export function ActionPanel({ background = 'dark-60', className, children }: ActionPanelProps) {
  const actionPanelClassName = clsx(
    styles.container,
    {
      [styles[background.split('-').join('--')]]: background,
    },
    className
  )
  return (
    <div className={actionPanelClassName} id="action-panel">
      {children}
    </div>
  )
}
