import clsx from 'clsx'

import { formatNumber, renderFormatNumber } from '@/utils/numbers'

import Show from '../Show'

import styles from './Delta.module.scss'

type DeltaProps = {
  value?: number
  className?: string
  isShowArrow?: boolean
}

export function Delta({ value, className, isShowArrow }: DeltaProps) {
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
          [styles.positive]: value > 0,
          [styles.negative]: value < 0,
        },
        className
      )}
      data-tooltip-content={isMinimal ? `${formatNumber(value)}%` : undefined}
      data-tooltip-id={isMinimal ? 'app-tooltip' : undefined}>
      <Show if={!isNeutral && value > 0 && !isShowArrow}>+</Show>
      <Show if={isMinimal}>~</Show>
      <Show if={!isNeutral}>
        {renderFormatNumber(shownValue, { options: { maximumFractionDigits: 2 } })}
      </Show>
      <Show if={isNeutral}>0</Show>%
    </span>
  )
}
