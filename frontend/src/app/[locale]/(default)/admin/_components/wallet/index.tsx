'use client'

import { FC } from 'react'

import clsx from 'clsx'
import { env } from 'next-runtime-env'
import { Address } from 'viem'
import { useBalance } from 'wagmi'

import AnimatedValue from '@/components/ui/AnimatedValue'
import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'
import { guruTestnet } from '@/config/wagmi'
import { formatNumber } from '@/utils/numbers'

import styles from './wallet.module.scss'

type PageCommunityWalletProps = {
  className?: string
}

export const PageCommunityWallet: FC<PageCommunityWalletProps> = ({ className }) => {
  const { data } = useBalance({
    address: (env('NEXT_PUBLIC_GURU_CHEST_ADDRESS') || '') as Address,
    chainId: guruTestnet.id,
    query: { refetchInterval: 60 * 1000 },
  })

  return (
    <Card className={clsx(styles.container, className)}>
      <div className={styles.header}>
        <Caption variant="body" size="lg" className={styles.title}>
          App Wallet
        </Caption>
      </div>

      <div className={styles.body}>
        <AnimatedValue
          className={styles.value}
          value={
            data?.formatted ? formatNumber(data?.formatted || '–', { notation: 'compact' }) : '–'
          }
        />
      </div>
    </Card>
  )
}
