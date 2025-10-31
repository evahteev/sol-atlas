import Delta from '@/components/atoms/Delta'
import TokenAsset from '@/components/atoms/TokenAsset'
import { renderFormatNumber } from '@/components/atoms/Value/utils'
import { TableColumnProps } from '@/components/ui/Table/types'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'

import styles from './content.module.scss'

export const tokenSelectorColumns = (chains?: ChainModel[]): TableColumnProps<TokenV3Model>[] => [
  {
    title: 'Token',
    render: ({ data }) => (
      <TokenAsset
        symbol={data.symbols}
        logo={data.logoURI}
        network={chains?.find((chain) => chain.name === data?.network) ?? { name: 'UNKN' }}
        className={styles.itemAsset}
        verified={data.verified}
      />
    ),
    className: styles.fixed,
  },
  {
    title: 'Price',
    render: ({ data }) => {
      return renderFormatNumber(data.priceUSD, { prefix: '$' })
    },
    type: 'number',
  },
  {
    render: ({ data }) => {
      return <Delta value={data.priceUSDChange24h * 100} />
    },
  },
  {
    title: 'Volume, 24h',
    render: ({ data }) => {
      return renderFormatNumber(data.volume24hUSD, { prefix: '$' })
    },
    type: 'number',
  },
  {
    render: ({ data }) => {
      return <Delta value={data.volumeUSDChange24h * 100} />
    },
  },
  {
    title: 'Liquidity',
    render: ({ data }) => {
      return renderFormatNumber(data.liquidityUSD, { prefix: '$' })
    },
    type: 'number',
  },
  {
    render: ({ data }) => {
      return <Delta value={data.liquidityUSDChange24h * 100} />
    },
  },
]
