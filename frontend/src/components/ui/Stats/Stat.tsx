import { ReactNode } from 'react'

import clsx from 'clsx'

import Value from '@/components/atoms/Value'
import { type ValueProps } from '@/components/atoms/Value/Value'

import Card from '../Card'
import Show from '../Show'

import styles from './Stat.module.scss'

export type StatProps = {
  title?: ReactNode
  className?: string
  content?: ReactNode
  children?: ReactNode
  value?: ValueProps
}

export function Stat({ title, className, children, content, value }: StatProps) {
  return (
    <Card className={clsx(styles.container, className)}>
      <Show if={title}>
        <div className={styles.header}>
          <strong className={styles.title}>{title}</strong>
        </div>
      </Show>
      <div className={styles.body}>
        {typeof value !== 'undefined' && (
          <Value {...value} className={clsx(styles.value, value.className)} size="md" />
        )}

        {content || children}
      </div>
    </Card>
  )
}
