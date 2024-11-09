'use client'

import { FC } from 'react'

import clsx from 'clsx'

import { Burns, Caption, Card } from '@/components/ui'
import { tGuru } from '@/config/wagmi'
import { useBurnsBalance } from '@/hooks/useBurnsBalance'
import { formatNumber } from '@/utils/numbers'

import { ProfileProp } from './Prop'

import styles from './Properties.module.scss'

type ProfileProperties = {
  className?: string
}

const unit = process.env.NEXT_PUBLIC_APP_CURRENCY ?? tGuru.nativeCurrency.symbol

export const ProfileProperties: FC<ProfileProperties> = ({ className }) => {
  const burnsBalance = useBurnsBalance()

  return (
    <Card className={clsx(styles.container, className)}>
      <ul className={styles.list}>
        <li className={clsx(styles.item, styles.burns)}>
          <ProfileProp caption={unit}>
            <Burns size="md" variant="numbers" strong>
              {burnsBalance === null ? '–' : formatNumber(burnsBalance)}
            </Burns>
            <sup>
              <Caption
                size="xs"
                variant="numbers"
                strong
                className={clsx(styles.delta, styles.positive)}>
                +230 <span className={styles.comment}>(1d)</span>
              </Caption>
            </sup>
          </ProfileProp>
        </li>

        <li className={styles.item}>
          <ProfileProp caption="Arena">
            <Caption size="md" variant="numbers" strong>
              #349
            </Caption>
          </ProfileProp>
        </li>

        <li className={styles.item}>
          <ProfileProp caption="Memes">
            <Caption size="md" variant="numbers" strong decorated="fire">
              349
            </Caption>
          </ProfileProp>
        </li>

        <li className={styles.item}>
          <ProfileProp caption="Votes">
            <Caption size="md" variant="numbers" strong decorated="fire">
              230
            </Caption>
          </ProfileProp>
        </li>

        <li className={styles.item}>
          <ProfileProp caption="Today PNL">
            <Caption
              size="sm"
              variant="numbers"
              strong
              className={clsx(styles.delta, styles.positive)}>
              +82,3892
            </Caption>
          </ProfileProp>
        </li>

        <li className={styles.item}>
          <ProfileProp caption="30 Days">
            <Caption
              size="sm"
              variant="numbers"
              strong
              className={clsx(styles.delta, styles.positive)}>
              +82,3892
            </Caption>
          </ProfileProp>
        </li>

        <li className={styles.item}>
          <ProfileProp caption="Cumulative PNL">
            <Caption
              size="sm"
              variant="numbers"
              strong
              className={clsx(styles.delta, styles.positive)}>
              +82,3892
            </Caption>
          </ProfileProp>
        </li>
      </ul>
    </Card>
  )
}
