import { ReactNode } from 'react'

import clsx from 'clsx'

import Show from '@/components/ui/Show'
import { formatNumber } from '@/utils/numbers'

import styles from './Delta.module.scss'

type DeltaProps = {
  value?: number
  className?: string
  isShowArrow?: boolean
  unit?: ReactNode
}

export function Delta({ value, className, isShowArrow, unit = '%' }: DeltaProps) {
  if (typeof value === 'undefined') {
    return null
  }

  const isNeutral = Math.abs(value) < 0.01
  const isMinimal = isNeutral && !!value

  const shownValue = isShowArrow ? Math.abs(value) : value

  return (
    <span
      className={clsx(
        styles.container,
        {
          [styles.positive]: !isNeutral && value > 0,
          [styles.negative]: !isNeutral && value < 0,
          [styles.neutral]: isNeutral,
        },
        className
      )}
      {...(isMinimal
        ? { 'data-tooltip-content': `${formatNumber(value)}%`, 'data-tooltip-id': 'app-tooltip' }
        : undefined)}>
      <Show if={!isNeutral && value > 0 && !isShowArrow}>+</Show>
      <Show if={isMinimal}>~</Show>
      <Show if={!isNeutral}>{formatNumber(shownValue, { maximumFractionDigits: 2 })}</Show>
      <Show if={isNeutral}>0</Show>
      {unit}
    </span>
  )
}
