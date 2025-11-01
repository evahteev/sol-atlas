import clsx from 'clsx'

import TokenAsset from '@/components/atoms/TokenAsset'
import { renderFormatNumber } from '@/components/atoms/Value/utils'
import { TableColumnProps } from '@/components/ui/Table/types'
import { ChainModel } from '@/models/chain'
import { TokenV3ModelWithBalances } from '@/models/token'

import styles from './TokenBalanceSelector.module.scss'

export const tokenBalanceColumns = ({
  chains = [],
  size = 'lg',
  isFetching = false,
}: {
  chains?: ChainModel[]
  size?: 'lg' | 'md' | 'sm'
  isFetching?: boolean
}): TableColumnProps<TokenV3ModelWithBalances, { balance?: number }>[] => [
  {
    title: 'Token',
    render: ({ data }) => (
      <TokenAsset
        size={size}
        symbol={data.token_symbol}
        logo={data.logoURI}
        network={chains?.find((chain) => chain.name === data?.network) ?? { name: 'UNKN' }}
        className={styles.itemAsset}
        verified={data.verified}
        price={data.priceUSD}
        delta={data.priceUSDChange24h}
      />
    ),
    className: clsx(styles.fixed, styles.colToken),
  },
  {
    title: 'Balance',
    render: ({ vars }) => {
      return renderFormatNumber(vars?.balance || 0, {
        className: clsx(styles.balance, { [styles.loading]: isFetching }),
      })
    },
    type: 'number',
  },
  {
    title: 'Value',
    render: ({ data, vars }) => {
      return renderFormatNumber((vars?.balance || 0) * (data.priceUSD || 0), { prefix: '$' })
    },
    type: 'number',
  },
]
