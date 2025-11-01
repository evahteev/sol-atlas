import clsx from 'clsx'

import Delta from '@/components/atoms/Delta'
import TokenAsset from '@/components/atoms/TokenAsset'
import { renderFormatNumber } from '@/components/atoms/Value/utils'
import { TableColumnProps } from '@/components/ui/Table/types'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'

import styles from '../assets/styles.module.scss'

export const topVolumeTokenListColumns = (
  chains: ChainModel[]
): TableColumnProps<TokenV3Model>[] => [
  {
    title: 'Asset',
    render: ({ data }) => (
      <TokenAsset
        symbol={data?.symbols || 'UNKNOWN'}
        logo={data?.logoURI || ''}
        network={chains.find((chain) => chain.name === data?.network) ?? { name: 'UNKN' }}
        className={styles.asset}
        verified={data.verified}
      />
    ),
    className: clsx(styles.fixed, styles.start, styles.separated),
  },
  {
    title: 'Price',
    render: ({ data }) =>
      renderFormatNumber(data?.priceUSD, {
        prefix: '$',
        options: { precisionMode: data?.priceUSD < 1 },
      }),
    type: 'number',
  },
  {
    render: ({ data }) => {
      return <Delta value={(data?.priceUSDChange24h || 0) * 100} />
    },
  },
  {
    title: 'Volume, 24h',
    render: ({ data }) =>
      renderFormatNumber(data?.volume24hUSD, {
        prefix: '$',
      }),
    type: 'number',
  },
  {
    title: 'Liquidity',
    render: ({ data }) =>
      renderFormatNumber(data?.liquidityUSD, {
        prefix: '$',
      }),
    type: 'number',
  },
  {
    render: ({ data }) => {
      return <Delta value={(data?.priceUSDChange24h || 0) * 100} />
    },
  },
]
