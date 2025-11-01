import { FC } from 'react'

import clsx from 'clsx'
import merge from 'lodash/merge'

import {
  fetchTokenProfileHistory,
  fetchTokenProfilePriceCharts,
  fetchTokenProfilePriceStatistics,
  fetchTokenProfilePriceTotals,
} from '@/actions/tokens'
import Delta from '@/components/atoms/Delta'
import Value from '@/components/atoms/Value'
import Meter from '@/components/ui/Meter'
import Show from '@/components/ui/Show'
import Stats from '@/components/ui/Stats'
import { TokenV3Model } from '@/models/token'
import { formatNumber } from '@/utils/numbers'

import { TokenOverviewStatsChart } from './chart'
import { TokenOverviewStatsCombo } from './combo'

import styles from './stats.module.scss'

const renderPriceSet = (price?: number, delta?: number) => (
  <TokenOverviewStatsCombo
    main={
      <>
        <Show if={price}>
          <Delta value={(delta ?? 0) * 100} className={styles.value} />
        </Show>
        <Show if={!price}>
          <span className={styles.na}>N/A</span>
        </Show>
      </>
    }
    aside={
      <Show if={price}>
        <Value value={formatNumber(price)} size="sm" prefix="$" className={styles.subvalue} />
      </Show>
    }
  />
)

const TokenOverviewStats: FC<{ token: TokenV3Model; className?: string }> = async ({
  token,
  className,
}) => {
  const [totals, charts, result, history] = await Promise.all([
    fetchTokenProfilePriceTotals(token.address, token.network),
    fetchTokenProfilePriceCharts(token.address, token.network),
    fetchTokenProfilePriceStatistics(token.address, token.network),
    fetchTokenProfileHistory(token.address, token.network),
  ])

  const transactionsChartValues = (charts?.transactionsChart ?? []).map(({ timestamp, value }) => ({
    timestamp,
    transactions: value,
  }))

  const holdersChartValues = (charts?.holdersChart ?? []).map(({ timestamp, value }) => ({
    timestamp,
    holders: value,
  }))

  const activityChartValues = (history ?? []).map(
    ({ date, dailyVolume, totalLiquidity, price, dailyTxns }) => ({
      timestamp: date,
      volume: dailyVolume,
      liquidity: totalLiquidity,
      price,
      transactions: dailyTxns,
    })
  )

  const chartValues = merge(transactionsChartValues, holdersChartValues, activityChartValues).sort(
    (a, b) => a.timestamp - b.timestamp
  )

  return (
    <div className={clsx(styles.container, className)}>
      <Stats
        items={[
          {
            className: clsx(styles.stat, styles.full),
            children: (
              <Stats
                items={[
                  {
                    title: 'Trading Volume, 24h',
                    value: {
                      value: formatNumber(token.volume24hUSD, { notation: 'compact' }),
                      prefix: '$',
                      delta: token.volumeUSDChange24h * 100,
                    },
                    className: styles.inner,
                  },
                  {
                    title: 'Transactions, 24h',
                    value: {
                      value: formatNumber(charts?.transactions24H),
                      delta: (charts?.transactions24HDailyDelta ?? 0) * 100,
                    },
                    className: styles.inner,
                  },
                ]}
              />
            ),
          },
          {
            className: styles.stat,
            title: 'Liquidity',
            content: (
              <TokenOverviewStatsCombo
                main={
                  <Value
                    value={formatNumber(token.liquidityUSD, { notation: 'compact' })}
                    size="md"
                    prefix="$"
                    className={styles.value}
                  />
                }
                aside={
                  <Delta
                    value={(token.liquidityUSDChange24h ?? 0) * 100}
                    className={styles.subvalue}
                  />
                }
              />
            ),
          },
          {
            className: styles.stat,
            title: 'FDV',
            content: (
              <TokenOverviewStatsCombo
                main={
                  <Value
                    value={formatNumber(totals?.fullyDilutedValuation, { notation: 'compact' })}
                    size="md"
                    prefix="$"
                    className={styles.value}
                  />
                }
                aside={
                  <Delta
                    value={(totals?.fullyDilutedValuationDailyDelta ?? 0) * 100}
                    className={styles.subvalue}
                  />
                }
              />
            ),
          },
          {
            className: styles.stat,
            title: 'Max Supply',
            content: (
              <TokenOverviewStatsCombo
                main={
                  <Value
                    value={formatNumber(totals?.maxSupply, { notation: 'compact' })}
                    size="md"
                    prefix="$"
                    className={styles.value}
                  />
                }
              />
            ),
          },
          {
            className: clsx(styles.stat, styles.full),
            title: 'Price',
            children: (
              <Stats
                items={[
                  {
                    title: '1H',
                    content: renderPriceSet(result?.hour_ago_price, result?.hour_ago_price_delta),
                    className: clsx(styles.stat, styles.inner),
                  },
                  {
                    title: '24H',
                    content: renderPriceSet(result?.day_ago_price, result?.day_ago_price_delta),
                    className: clsx(styles.stat, styles.inner),
                  },
                  {
                    title: '7D',
                    content: renderPriceSet(result?.week_ago_price, result?.week_ago_price_delta),
                    className: clsx(styles.stat, styles.inner),
                  },
                  {
                    title: 'YTD',
                    content: renderPriceSet(
                      result?.year_to_date_price,
                      result?.year_to_date_price_delta
                    ),
                    className: clsx(styles.stat, styles.inner),
                  },
                ]}
              />
            ),
          },
          {
            className: styles.stat,
            title: 'Holders',
            content: (
              <TokenOverviewStatsCombo
                main={
                  <Value
                    value={formatNumber(charts?.totalHolders, { notation: 'compact' })}
                    size="md"
                    prefix="$"
                    className={styles.value}
                  />
                }
                aside={
                  <Show if={charts?.totalHoldersDelta}>
                    <Delta value={charts?.totalHoldersDelta} className={styles.subvalue} />
                  </Show>
                }
              />
            ),
          },
          {
            className: styles.stat,
            title: 'Holders Making Money',
            content: (
              <Meter
                showTitles
                value={[
                  {
                    title: 'In',
                    value: (charts?.holdersMakingMoney?.in ?? 0) * 100,
                    className: styles.in,
                  },
                  {
                    title: 'At',
                    value: (charts?.holdersMakingMoney?.at_money ?? 0) * 100,
                    className: styles.at,
                  },
                  {
                    title: 'Out',
                    value: (charts?.holdersMakingMoney?.out ?? 0) * 100,
                    className: styles.out,
                  },
                ]}
              />
            ),
          },
          {
            title: 'Token Trends',
            className: clsx(styles.stat, styles.full),
            content: (
              <TokenOverviewStatsChart className={styles.trends} data={chartValues} token={token} />
            ),
          },
        ]}
      />
    </div>
  )
}

export default TokenOverviewStats
