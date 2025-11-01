import { CSSProperties } from 'react'

import clsx from 'clsx'

import { formatNumber } from '@/utils/numbers'

import Show from '../Show'

import styles from './Meter.module.scss'

type MeterValue = {
  title: string
  value: number
  className?: string
}

type MeterProps = {
  value: MeterValue | MeterValue[]
  className?: string
  showTitles?: boolean
  max?: number
  min?: number
  prefix?: string
  suffix?: string
}

export function Meter({
  value,
  max = 100,
  min = 0,
  showTitles,
  className,
  prefix,
  suffix,
}: MeterProps) {
  if (min >= max) {
    return null
  }

  const values = (Array.isArray(value) ? value : [value]).map((item) => ({
    ...item,
    percent: Math.min((item.value / (max - min)) * 100, 100),
  }))
  const isFull = values.reduce((acc, val) => acc + val.value, 0) >= max

  return (
    <div className={clsx(styles.container, className)}>
      <Show if={showTitles}>
        <div className={styles.header}>
          {values.map((val, idx) => {
            return (
              <span key={idx} className={styles.title}>
                <span className={styles.caption}>{val.title}</span>
                <span className={clsx(styles.value, val.className)}>
                  {formatNumber(val.percent, { maximumFractionDigits: 2 })}%
                </span>
              </span>
            )
          })}
        </div>
      </Show>

      <div className={styles.body}>
        <div className={clsx(styles.meter, { [styles.full]: isFull })}>
          {values
            .filter((val) => val?.value)
            .map((val, idx) => {
              return (
                <span
                  data-tooltip-content={`${val.title ? `${val.title}:` : ''} ${
                    prefix || ''
                  }${formatNumber(val.value)}${suffix || ''}${val.percent === val.value ? '%' : ` (${formatNumber(val.percent)}%)`}`}
                  data-tooltip-id="app-tooltip"
                  key={idx}
                  className={clsx(styles.bar, val.className)}
                  style={{ '--_width': `${val.percent}%` } as CSSProperties}
                />
              )
            })}
        </div>
      </div>
    </div>
  )
}
