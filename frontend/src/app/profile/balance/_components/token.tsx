import Image from 'next/image'

import { FC } from 'react'

import clsx from 'clsx'

import { Burns, Button, Caption, Show } from '@/components/ui'
import { formatNumber } from '@/utils/numbers'

import styles from './token.module.scss'

type ProfileBalanceTokenProps = {
  className?: string
  image: string
} & (
  | {
      burns: number
      token?: never
    }
  | {
      burns?: never
      token: {
        symbol: string
        amount: number
        value: number
        pnlDelta: number
      }
    }
)

export const ProfileBalanceToken: FC<ProfileBalanceTokenProps> = (props) => {
  return (
    <div className={clsx(styles.container, props.className)}>
      <Image src={props.image} alt="" width={160} height={160} className={styles.image} />
      <div className={styles.body}>
        <Show if={props.burns}>
          <Burns size="md" variant="numbers" strong>
            {formatNumber(props.burns)}
          </Burns>
        </Show>
        <Show if={props.token}>
          <div className={styles.token}>
            <Caption variant="numbers" size="md" className={styles.tokenAmount}>
              {props.token?.amount}
            </Caption>{' '}
            <Caption variant="numbers" size="md" className={styles.tokenSymbol}>
              {props.token?.symbol}
            </Caption>
          </div>
          <div className={styles.meta}>
            <Burns size="md" className={styles.tokenAmount}>
              ~{props.token?.value}
            </Burns>{' '}
            <Caption variant="body" size="md" className={styles.tokenAmount}>
              (+{props.token?.amount}% PNL)
            </Caption>
          </div>
        </Show>
      </div>
      <div className={styles.footer}>
        <Show if={props.burns}>
          <Button size="md" className={clsx(styles.action, styles.send)}>
            Send
          </Button>
        </Show>
        <Show if={props.token}>
          <Button variant="success" size="md" className={clsx(styles.action, styles.buy)}>
            Buy
          </Button>
          <Button variant="danger" size="md" className={clsx(styles.action, styles.sell)}>
            Sell
          </Button>
        </Show>
      </div>
    </div>
  )
}
