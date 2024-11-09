'use client'

import Link from 'next/link'

import { FC } from 'react'

import clsx from 'clsx'

import JazzIcon from '@/components/atoms/JazzIcon'
import { jsNumberForAddress } from '@/components/atoms/JazzIcon/utils'
import { Burns, Card, Show } from '@/components/ui'
import { tGuru } from '@/config/wagmi'
import { useBurnsBalance } from '@/hooks/useBurnsBalance'
import { useWalletAddress } from '@/hooks/useWalletAddress'
import { formatNumber } from '@/utils/numbers'

import styles from './ProfileBar.module.scss'

export const ProfileBar: FC<{ className: string }> = ({ className }) => {
  const walletAddress = useWalletAddress()
  const burnsBalance = useBurnsBalance()

  return (
    <Card className={clsx(styles.container, className)} id="profile-bar">
      <Show if={walletAddress}>
        <Link className={styles.link} href="/profile/wallets">
          <JazzIcon
            size={48}
            seed={jsNumberForAddress(walletAddress ?? '')}
            className={styles.avatar}
          />
        </Link>
      </Show>
      <Link
        href={`${tGuru.blockExplorers.default.url}/address/${walletAddress}`}
        target="_blank"
        rel="noopener noreferrer">
        <Burns size="md" variant="numbers" strong={true}>
          {burnsBalance === null ? '–' : formatNumber(burnsBalance)}
        </Burns>
      </Link>
    </Card>
  )
}
