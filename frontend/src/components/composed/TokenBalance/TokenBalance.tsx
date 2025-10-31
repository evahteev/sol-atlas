import { FC } from 'react'

import clsx from 'clsx'

import TokenAsset from '@/components/atoms/TokenAsset'
import Value from '@/components/atoms/Value'
import { TokenV3ModelWithBalances } from '@/models/token'
import { formatNumber } from '@/utils/numbers'

import styles from './TokenBalance.module.scss'

type TokenBalanceProps = {
  className?: string
  tokenBalance?: TokenV3ModelWithBalances
  chain?: {
    name: string
    color?: string
  }
  isLoading?: boolean
  size?: 'sm' | 'md' | 'lg'
}

export const TokenBalance: FC<TokenBalanceProps> = ({
  className,
  tokenBalance,
  chain,
  isLoading,
  size = 'lg',
}) => {
  return (
    <div className={clsx(styles.container, { [styles.loading]: isLoading }, className)}>
      <TokenAsset
        href={
          tokenBalance
            ? `/token/${tokenBalance?.network.toLocaleLowerCase()}/${tokenBalance?.address.toLocaleLowerCase()}`
            : undefined
        }
        symbol={tokenBalance?.token_symbol || 'UNKNOWN'}
        logo={tokenBalance?.logoURI || ''}
        size={size}
        network={chain ?? { name: 'UNKN' }}
        price={tokenBalance?.priceUSD ?? 0}
        delta={(tokenBalance?.priceUSDChange24h ?? 0) * 100}
        className={styles.asset}
        verified={tokenBalance?.verified}
      />

      <div className={styles.balances}>
        <span className={styles.amount}>{formatNumber(tokenBalance?.balance ?? 0)}</span>{' '}
        <Value
          prefix="$"
          className={styles.value}
          value={formatNumber((tokenBalance?.balance ?? 0) * (tokenBalance?.priceUSD ?? 0))}
        />
      </div>
    </div>
  )
}
