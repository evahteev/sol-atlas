import { PropsWithChildren, ReactNode } from 'react'

import clsx from 'clsx'

import Show from '@/components/ui/Show'

import Delta from '../Delta'

import styles from './Value.module.scss'

export type ValueSize = 'md' | 'lg' | 'sm'

export type ValueProps = PropsWithChildren & {
  tooltip?: string
  value?: ReactNode
  prefix?: ReactNode
  suffix?: ReactNode
  className?: string
  delta?: number
  size?: ValueSize
}

export function Value({
  tooltip,
  value,
  prefix,
  suffix,
  delta,
  size,
  className,
  children,
}: ValueProps) {
  return (
    <span
      className={clsx(styles.container, className)}
      data-tooltip-html={tooltip}
      data-tooltip-id={tooltip ? 'app-tooltip' : undefined}>
      <span className={clsx(styles.value, { [styles[size ?? '']]: !!size })}>
        <Show if={prefix}>
          <span className={styles.prefix}>{prefix}</span>
        </Show>
        {value ?? children}
        <Show if={suffix}>
          <span className={styles.suffix}>{suffix}</span>
        </Show>
      </span>

      <Show if={typeof delta !== 'undefined'}>
        {' '}
        <Delta value={delta} className={styles.delta} />
      </Show>
    </span>
  )
}
