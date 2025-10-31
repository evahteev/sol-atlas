'use client'

import { FC, createElement } from 'react'

import clsx from 'clsx'

import JazzIcon from '@/components/atoms/JazzIcon'
import { jsNumberForAddress } from '@/components/atoms/JazzIcon/utils'
import Loader from '@/components/atoms/Loader'
import Value from '@/components/atoms/Value'
import { useWalletTotals } from '@/hooks/useWalletTotals'
import { ChainModel } from '@/models/chain'
import { formatNumber } from '@/utils/numbers'
import { getShortAddress } from '@/utils/strings'

import styles from './ProfileAccount.module.scss'

type ProfileAccountProps = {
  className?: string
  address: string
  chains?: ChainModel[]
  onClick?: () => void
}

export const ProfileAccount: FC<ProfileAccountProps> = ({
  className,
  address,
  onClick,
  chains,
}) => {
  const { tokens, natives, isFetching } = useWalletTotals({
    address,
    chains: chains || [],
    refetchInterval: 1 * 60 * 1000, // 1 minute
    enabled: !!address,
  })

  const totalValue = [...tokens, ...natives].reduce(
    (acc, token) => acc + (token.balance || 0) * (token.priceUSD || 0),
    0
  )

  if (!address) {
    return null
  }

  return createElement(
    onClick ? 'button' : 'div',
    {
      className: clsx(styles.container, className),
      onClick,
    },
    <>
      <JazzIcon seed={jsNumberForAddress(address)} className={styles.avatar} />

      <div className={styles.address}>{getShortAddress(address)}</div>

      <Value
        className={styles.balance}
        value={
          isFetching && !totalValue ? (
            <Loader className={styles.loader} />
          ) : (
            formatNumber(totalValue)
          )
        }
        prefix="$"
      />
    </>
  )
}
