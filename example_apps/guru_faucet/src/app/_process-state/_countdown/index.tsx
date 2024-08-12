'use client'

import { FC, ReactNode, useCallback, useState } from 'react'

import { useIntervalWhen } from 'rooks'

interface CountdownTimerProps {
  futureTimestamp: number | string | Date
  className?: string
  prefix?: ReactNode
  suffix?: ReactNode
  showZero?: boolean
  showUnits?: boolean
}

interface TimeLeft {
  days: number
  hours: number
  minutes: number
  seconds: number
}

const formatTime = (time: number, suffix: string, showZero = true) =>
  time === 0 && !showZero ? '' : `${time < 10 ? `0${time}` : time.toString()}${suffix}`

const CountdownTimer: FC<CountdownTimerProps> = ({
  futureTimestamp,
  className,
  prefix,
  suffix,
  showZero,
  showUnits = true,
}) => {
  const calculateTimeLeft = useCallback((): TimeLeft => {
    const futureDate = new Date(futureTimestamp).getTime()
    const currentDate = new Date().getTime()
    const difference = futureDate - currentDate

    if (difference > 0) {
      return {
        days: Math.floor(difference / (1000 * 60 * 60 * 24)),
        hours: Math.floor((difference / (1000 * 60 * 60)) % 24),
        minutes: Math.floor((difference / (1000 * 60)) % 60),
        seconds: Math.floor((difference / 1000) % 60),
      }
    } else {
      return {
        days: 0,
        hours: 0,
        minutes: 0,
        seconds: 0,
      }
    }
  }, [futureTimestamp])

  const [timeLeft, setTimeLeft] = useState<TimeLeft>({
    days: 0,
    hours: 0,
    minutes: 0,
    seconds: 0,
  })

  useIntervalWhen(
    () => {
      setTimeLeft(calculateTimeLeft())
    },
    1000,
    true,
    true
  )

  return (
    <span className={className}>
      {prefix} {formatTime(timeLeft.days, `${showUnits ? 'd' : ''}:`, false)}
      {formatTime(timeLeft.hours, `${showUnits ? 'h' : ''}:`, showZero || !!timeLeft.days)}
      {formatTime(timeLeft.minutes, `${showUnits ? 'm' : ''}:`, showZero || !!timeLeft.hours)}
      {formatTime(timeLeft.seconds, showUnits ? 's' : '')} {suffix}
    </span>
  )
}

export default CountdownTimer
