import clsx from 'clsx'

import Delta from '@/components/atoms/Delta'
import SimpleLineChart from '@/components/atoms/SimpleLineChart'
import TokenAsset from '@/components/atoms/TokenAsset'
import { renderFormatNumber } from '@/components/atoms/Value/utils'
import { TableColumnProps } from '@/components/ui/Table/types'
import { ChainModel } from '@/models/chain'
import { TrendingToken } from '@/models/token'

import styles from '../assets/styles.module.scss'

export const trendingTokenListColumns = (
  chains: ChainModel[]
): TableColumnProps<TrendingToken>[] => [
  {
    title: 'Asset',
    render: ({ data }) => (
      <TokenAsset
        symbol={data?.symbol || 'UNKNOWN'}
        logo={data?.logoURI || ''}
        network={chains.find((chain) => chain.name === data?.network) ?? { name: 'UNKN' }}
        className={styles.asset}
        verified={true}
      />
    ),
    className: clsx(styles.fixed, styles.start, styles.separated),
  },
  {
    title: 'Price',
    render: ({ data }) =>
      renderFormatNumber(data?.current?.priceUSD, {
        prefix: '$',
      }),
    type: 'number',
  },
  {
    title: '24h',
    render: ({ data }) => {
      return <Delta value={(data?.trending?.day.priceMove || 0) * 100} />
    },
    type: 'number',
  },
  {
    title: '7d',
    render: ({ data }) => <Delta value={(data?.trending?.week.priceMove || 0) * 100} />,
    type: 'number',
  },
  {
    title: '30d',
    render: ({ data }) => <Delta value={(data?.trending?.month.priceMove || 0) * 100} />,
    type: 'number',
  },
  {
    title: 'Last 7 days',
    render: ({ data }) =>
      data?.chart && (
        <SimpleLineChart
          className={styles.chart}
          values={data?.chart.map((c) => c.price)}
          color={
            data?.trending.week.priceMove >= 0
              ? 'var(--color-positive,green)'
              : 'var(--color-negative,red)'
          }
          zeroBased={false}
          smooth
        />
      ),
  },
  {
    title: 'Volume',
    render: ({ data }) =>
      renderFormatNumber(data?.current?.volumeUSD, {
        prefix: '$',
      }),
    type: 'number',
  },
  {
    title: '24h',
    render: ({ data }) => {
      return <Delta value={(data?.trending?.day.volumeMove || 0) * 100} />
    },
    type: 'number',
  },
  {
    title: '7d',
    render: ({ data }) => <Delta value={(data?.trending?.week.volumeMove || 0) * 100} />,
    type: 'number',
  },
  {
    title: '30d',
    render: ({ data }) => <Delta value={(data?.trending?.month.volumeMove || 0) * 100} />,
    type: 'number',
  },
  {
    title: 'Last 7 days',
    render: ({ data }) =>
      data?.chart && (
        <SimpleLineChart
          className={styles.chart}
          values={data?.chart.map((c) => c.price)}
          color={
            data?.trending.week.priceMove >= 0
              ? 'var(--color-positive,green)'
              : 'var(--color-negative,red)'
          }
          zeroBased={false}
          smooth
        />
      ),
  },
]
