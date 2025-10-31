'use client'

import { FC, ReactNode, useState } from 'react'

import clsx from 'clsx'
import { useIntervalWhen } from 'rooks'

import Show from '../Show'

import styles from './TimerCountdown.module.scss'

type TimerCountdownProps = {
  className?: string
  timestamp: number | string | Date
  prefix?: ReactNode
  suffix?: ReactNode
  showZero?: boolean
  showUnits?: boolean
  isCompact?: boolean
}

const formatTime = (time: number, suffix: string, showZero = true, isCompact = false) =>
  time === 0 && !showZero ? '' : `${`${time}`.padStart(2, isCompact ? '' : '0')}${suffix}`

const TimerCountdown: FC<TimerCountdownProps> = ({
  timestamp,
  className,
  prefix,
  suffix,
  showUnits = true,
  showZero,
  isCompact,
}) => {
  const [seconds, setSeconds] = useState<number | null>(null)
  const dueDate = new Date(timestamp)

  useIntervalWhen(
    () => {
      if (!timestamp) {
        return
      }

      setSeconds(Math.round(Math.floor(dueDate.getTime() - new Date().getTime()) / 1000))
    },
    1000,
    true,
    true
  )

  if (seconds === null) {
    return null
  }

  const secondsAbs = Math.abs(seconds)

  const diff = {
    days: Math.floor(secondsAbs / (60 * 60 * 24)),
    hours: Math.floor((secondsAbs / (60 * 60)) % 24),
    minutes: Math.floor((secondsAbs / 60) % 60),
    seconds: Math.floor(secondsAbs % 60),
  }

  return (
    <span className={clsx(styles.container, className)}>
      {prefix}{' '}
      <Show if={diff.days}>
        {diff.days}
        {showUnits ? 'd ' : ''}
      </Show>
      {(!isCompact || (isCompact && !diff.days)) &&
        formatTime(diff.hours, `${showUnits ? 'h ' : ''}`, showZero || !!diff.days, isCompact)}
      {(!isCompact || (isCompact && !diff.hours)) &&
        formatTime(diff.minutes, `${showUnits ? 'm ' : ''}`, showZero || !!diff.hours, isCompact)}
      {(!isCompact || (isCompact && !diff.minutes)) &&
        formatTime(diff.seconds, showUnits ? 's ' : '', true, isCompact)}{' '}
      {suffix}
    </span>
  )
}

export default TimerCountdown
