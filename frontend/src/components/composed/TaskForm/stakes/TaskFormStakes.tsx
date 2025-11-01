import { FC } from 'react'

import Properties from '@/components/atoms/Properties'
import Button from '@/components/ui/Button'
import Message from '@/components/ui/Message'
import Show from '@/components/ui/Show'
import TimerCountdown from '@/components/ui/TimerCountdown'
import { getShortDate } from '@/utils/dates'
import { formatNumber } from '@/utils/numbers'

import styles from './TaskFormStakes.module.scss'

type TaskFormStakesItemProps = {
  amount: number
  rewards: number
  start_time: number
  lock_period: number
  withdraw_time?: number
}

type TaskFormStakesProps = {
  className?: string
  name: string
  caption?: string | null
  data?: TaskFormStakesItemProps
}

export const TaskFormStakes: FC<TaskFormStakesProps> = ({ data }) => {
  const currentStake = data

  const startTime = 1000 * (currentStake?.start_time || 0)
  const endTime = 1000 * ((currentStake?.start_time || 0) + (currentStake?.lock_period || 0))
  const timeLeft = endTime - Date.now()

  const withdrawTime = 1000 * (currentStake?.withdraw_time || 0)
  const withdrawTimeLeft = withdrawTime - Date.now()

  return (
    <>
      <Show if={currentStake}>
        <Message className={styles.stake}>
          <Properties
            className={styles.properties}
            items={[
              {
                caption: 'Current Amount',
                value: formatNumber(currentStake?.amount),
              },
              {
                caption: 'Start Time',
                value: getShortDate(startTime),
              },
              {
                caption: 'Lock Period',
                value: `${(currentStake?.lock_period || 0) / 60 / 60 / 24} Days`,
              },
              {
                caption: 'Pending Rewards',
                value: formatNumber(currentStake?.rewards || 0),
              },
            ]}
          />
          <div className={styles.actions}>
            <Button
              variant="primary"
              size="md"
              type="submit"
              caption={'Claim Reward'}
              value={'true'}
              name={'action_claim'}
              className={styles.action}
            />
            <Button
              variant="primary"
              size="md"
              type="submit"
              caption={
                withdrawTime > 0 && withdrawTimeLeft < 0 ? (
                  'Withdraw'
                ) : withdrawTime > 0 && withdrawTimeLeft >= 0 ? (
                  <TimerCountdown
                    timestamp={withdrawTime}
                    isCompact
                    prefix={'Withdraw Cool Off ends in '}
                  />
                ) : withdrawTime === 0 && timeLeft < 0 ? (
                  'Initiate Withdrawal'
                ) : (
                  <TimerCountdown timestamp={endTime} isCompact prefix={'Withdraw in '} />
                )
              }
              value={'true'}
              name={'action_withdraw'}
              className={styles.action}
              isDisabled={timeLeft > 0 || withdrawTimeLeft > 0}
            />
          </div>
        </Message>
      </Show>
    </>
  )
}
