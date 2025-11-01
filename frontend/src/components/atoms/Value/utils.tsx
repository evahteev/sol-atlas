import { ReactNode } from 'react'

import clsx from 'clsx'

import { FormatNumberOptions, formatNumber } from '@/utils/numbers'

import { Value } from './Value'

import styles from './Value.module.scss'

export const renderFormatNumber = (
  value?: number | null,
  props: {
    infinityLimit?: number
    options?: FormatNumberOptions
    prefix?: ReactNode
    suffix?: ReactNode
    delta?: number
    className?: string
  } = { options: { keepTrailingZeroes: false } }
) => {
  if (typeof value === 'undefined' || value === null) {
    return <span className={clsx(styles.sign, props?.className)}>N/A</span>
  }

  if (value >= (props.infinityLimit ?? 10 ** 12)) {
    return (
      <span
        className={props?.className}
        data-tooltip-content={formatNumber(value, {
          notation: 'standard',
          keepTrailingZeroes: props?.options?.keepTrailingZeroes,
          precisionMode: props?.options?.precisionMode,
        })}
        data-tooltip-id="app-tooltip">
        ∞
      </span>
    )
  }

  return (
    <Value
      className={props?.className}
      value={formatNumber(value, props?.options)}
      prefix={props?.prefix}
      suffix={props?.suffix}
      delta={props?.delta}
    />
  )
}
