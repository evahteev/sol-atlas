import { ReactNode } from 'react'

import clsx from 'clsx'

import Delta from '../Delta'
import Show from '../Show'

import styles from './Value.module.scss'

export type ValueSize = 'md' | 'lg' | 'sm'

export type ValueProps = {
  tooltip?: string
  value: ReactNode
  prefix?: ReactNode
  suffix?: ReactNode
  className?: string
  delta?: number
  size?: ValueSize
}

export function Value({ tooltip, value, prefix, suffix, delta, size, className }: ValueProps) {
  return (
    <span
      className={clsx(styles.container, className)}
      data-tooltip-html={tooltip}
      data-tooltip-id={tooltip ? 'app-tooltip' : undefined}>
      <span className={clsx(styles.value, { [styles[size ?? '']]: !!size })}>
        <Show if={prefix}>
          <span className={styles.prefix}>{prefix}</span>
        </Show>
        {value}
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
