import clsx from 'clsx'

import TokenAsset from '@/components/atoms/TokenAsset'
import Value from '@/components/atoms/Value'
import { TableColumnProps } from '@/components/ui/Table/types'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'
import { formatNumber } from '@/utils/numbers'

import styles from './TokenSelector.module.scss'

export const tokenSelectorColumns = ({
  chains = [],
  size = 'lg',
  isFetching = false,
}: {
  chains?: ChainModel[]
  size?: 'lg' | 'md' | 'sm'
  isFetching?: boolean
}): TableColumnProps<TokenV3Model, { balance?: number }>[] => [
  {
    title: 'Token',
    render: ({ data }) => (
      <TokenAsset
        size={size}
        symbol={data.symbols}
        logo={data.logoURI}
        network={chains?.find((chain) => chain.name === data?.network) ?? { name: 'UNKN' }}
        className={styles.itemAsset}
        verified={data.verified}
        price={data.priceUSD}
        delta={data.priceUSDChange24h * 100}
      />
    ),
    className: clsx(styles.fixed, styles.colToken),
  },

  {
    title: 'Balance',
    render: ({ data, vars }) => {
      if (isFetching) {
        return (
          <div className={clsx(styles.balance, { [styles.loading]: isFetching })}>
            <Value value={0} className={styles.amount} />{' '}
            <Value value={0} prefix="$" className={styles.value} />
          </div>
        )
      }

      if (!vars?.balance) {
        return null
      }

      return (
        <div className={styles.balance}>
          <Value value={formatNumber(vars.balance || 0)} className={styles.amount} />{' '}
          <Value
            value={formatNumber((vars.balance || 0) * (data.priceUSD || 0))}
            prefix="$"
            className={styles.value}
          />
        </div>
      )
    },
    type: 'number',
  },
]
