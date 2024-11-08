'use client'

import { FC, ReactNode, useState } from 'react'

import clsx from 'clsx'
import { useIntervalWhen } from 'rooks'

import styles from './TimerCountdown.module.scss'

type TimerCountdownProps = {
  className?: string
  timestamp: number | string | Date
  prefix?: ReactNode
  suffix?: ReactNode
  showZero?: boolean
  showUnits?: boolean
}

const formatTime = (time: number, suffix: string, showZero = true) =>
  time === 0 && !showZero ? '' : `${time < 10 ? `0${time}` : time.toString()}${suffix}`

const TimerCountdown: FC<TimerCountdownProps> = ({
  timestamp,
  className,
  prefix,
  suffix,
  showUnits = true,
  showZero,
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
      {prefix} {formatTime(diff.days, `${showUnits ? 'd ' : ''}`, false)}
      {formatTime(diff.hours, `${showUnits ? 'h ' : ''}`, showZero || !!diff.days)}
      {formatTime(diff.minutes, `${showUnits ? 'm ' : ''}`, showZero || !!diff.hours)}
      {formatTime(diff.seconds, showUnits ? 's ' : '')} {suffix}
    </span>
  )
}

export default TimerCountdown
