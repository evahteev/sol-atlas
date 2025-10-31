import React, { FC, ReactNode } from 'react'

import clsx from 'clsx'

import Value from '@/components/atoms/Value'
import AnimatedValue from '@/components/ui/AnimatedValue'
import Show from '@/components/ui/Show'
import { getAsArray } from '@/utils'
import { formatNumber } from '@/utils/numbers'

import styles from './DashboardWidgetCounter.module.scss'

export type DashboardWidgetCounterDeltaProps = {
  value: number | null
  suffix?: ReactNode
  unit?: ReactNode
}

export type DashboardWidgetCounterProps = {
  isLoading?: boolean
  value: number | null
  delta?: number | DashboardWidgetCounterDeltaProps | DashboardWidgetCounterDeltaProps[]
}

export const DashboardWidgetCounter: FC<DashboardWidgetCounterProps> = (props) => {
  const { value = null, delta, isLoading } = props

  const deltas =
    typeof delta === 'number' ? [{ value: delta }] : delta ? getAsArray(delta) : undefined

  return (
    <div className={styles.container}>
      <AnimatedValue
        value={value === null ? '–' : formatNumber(value, { notation: 'compact' })}
        className={clsx(styles.value, { [styles.loading]: isLoading })}
      />
      <Show if={deltas?.length}>
        <span className={styles.appendix}>
          {deltas?.map(({ value: deltaValue = null, suffix, unit }, idx) => {
            return (
              <React.Fragment key={idx}>
                {' '}
                <Value
                  value={
                    <>
                      {deltaValue === null
                        ? '–'
                        : formatNumber(deltaValue, { signDisplay: 'always', notation: 'compact' })}
                      {unit}
                    </>
                  }
                  suffix={suffix}
                  className={clsx(styles.delta, {
                    [styles.loading]: isLoading,
                    [styles.positive]: (deltaValue || 0) > 0,
                    [styles.negative]: (deltaValue || 0) < 0,
                  })}
                />
              </React.Fragment>
            )
          })}
        </span>
      </Show>

      <Show if={!delta}>&nbsp;</Show>
    </div>
  )
}
