import clsx from 'clsx'

import Delta from '@/components/atoms/Delta'
import SimpleLineChart from '@/components/atoms/SimpleLineChart'
import TokenAsset from '@/components/atoms/TokenAsset'
import Value from '@/components/atoms/Value'
import { renderFormatNumber } from '@/components/atoms/Value/utils'
import { TableColumnProps } from '@/components/ui/Table/types'
import { ChainModel } from '@/models/chain'
import { TokenProfile } from '@/models/token'

import styles from './table.module.scss'

const getLV24Ratio = (data?: TokenProfile) => {
  const lv24ratio = (data?.liquidity_usd || 0) / (data?.current?.volume_usd || 1) || 0

  return (
    <Value
      value={
        lv24ratio < 0.0000001
          ? '~0'
          : lv24ratio.toLocaleString('en-US', {
              maximumFractionDigits: lv24ratio > 1 ? 2 : 7,
            })
      }
    />
  )
}

export const tokenListColumns = (chains: ChainModel[]): TableColumnProps<TokenProfile>[] => [
  {
    title: 'Asset',
    render: ({ data }) => (
      <TokenAsset
        symbol={data?.symbol || 'UNKNOWN'}
        logo={data?.logo_uri || ''}
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
      renderFormatNumber(data?.current?.price_usd, {
        prefix: '$',
      }),
    type: 'number',
  },
  {
    title: '24h',
    render: ({ data }) => {
      return <Delta value={(data?.trending?.day.price_move || 0) * 100} />
    },
    type: 'number',
  },
  {
    title: '7d',
    render: ({ data }) => <Delta value={(data?.trending?.week.price_move || 0) * 100} />,
    type: 'number',
  },
  {
    title: '30d',
    render: ({ data }) => <Delta value={(data?.trending?.month.price_move || 0) * 100} />,
    type: 'number',
  },
  {
    title: 'YTD',
    render: ({ data }) => <Delta value={(data?.trending?.year.price_move || 0) * 100} />,
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
            data?.trending.week.price_move >= 0
              ? 'var(--color-positive,green)'
              : 'var(--color-negative,red)'
          }
          zeroBased={false}
          smooth
        />
      ),
  },
  {
    title: 'All-Time High Price',
    render: ({ data }) => renderFormatNumber(data?.price_usd_max),
    type: 'number',
    className: styles.separated,
  },
  {
    title: 'Trading Volume, 24h',
    render: ({ data }) => renderFormatNumber(data?.current?.volume_usd, { prefix: '$' }),
    type: 'number',
    className: styles.separated,
  },
  {
    title: 'Fully Diluted Valuation',
    render: ({ data }) => renderFormatNumber(data?.fully_diluted_valuation, { prefix: '$' }),
    type: 'number',
  },
  {
    render: ({ data }) => <Delta value={data?.fully_diluted_valuation_daily_delta * 100} />,
    className: styles.separated,
  },
  {
    title: 'Max Supply',
    render: ({ data }) => renderFormatNumber(data?.token_supply),
    type: 'number',
    className: styles.separated,
  },
  {
    title: 'Liquidity, 24h',
    render: ({ data }) => renderFormatNumber(data?.liquidity_usd, { prefix: '$' }),
    type: 'number',
  },
  {
    render: ({ data }) => <Delta value={data?.liquidity_usd_change24h * 100} />,
  },
  {
    title: 'Liquidity/Volume24h',
    render: ({ data }) => getLV24Ratio(data),
    type: 'number',
    className: styles.separated,
  },
  {
    title: 'Transactions, 24h',
    render: ({ data }) => renderFormatNumber(data.txns24h),
    type: 'number',
    className: styles.separated,
  },
  {
    render: ({ data }) => <Delta value={data?.txns24h_change * 100} />,
  },
  {
    title: 'Holders',
    render: ({ data }) => renderFormatNumber(data.holders_count),
    type: 'number',
  },
]
