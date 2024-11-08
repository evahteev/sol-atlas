'use client'

import Link from 'next/link'

import { FC } from 'react'

import { Burns } from '@/components/ui'
import { tGuru } from '@/config/wagmi'
import { useBurnsBalance } from '@/hooks/useBurnsBalance'
import { useWalletAddress } from '@/hooks/useWalletAddress'
import { formatNumber } from '@/utils/numbers'

type ProfileWalletsBalanceProps = {
  className?: string
}

export const ProfileWalletsBalance: FC<ProfileWalletsBalanceProps> = ({ className }) => {
  const walletAddress = useWalletAddress()
  const burnsBalance = useBurnsBalance()

  return (
    <Link
      href={`${tGuru.blockExplorers.default.url}/address/${walletAddress}`}
      target="_blank"
      rel="noopener noreferrer">
      <Burns size="md" variant="numbers" strong={true} className={className}>
        {burnsBalance === null ? '–' : formatNumber(burnsBalance)}
      </Burns>
    </Link>
  )
}
