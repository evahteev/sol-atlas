'use client'

import { FC } from 'react'

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { TokenV3Model } from '@/models/token'
import { getDistinctColors } from '@/utils/colors'
import { getDate } from '@/utils/dates'
import { formatNumber } from '@/utils/numbers'
import { getTokenSymbolsString } from '@/utils/tokens'

import styles from './stats.module.scss'

export const TokenOverviewStatsChart: FC<{
  token: TokenV3Model
  className?: string
  data: Array<Record<string, number> & { timestamp: number }>
}> = ({ token, data }) => {
  const chartTopics = {
    transactions: 'TX Count',
    holders: 'Holders Count',
    volume: 'Trading Volume, 24h, $',
    liquidity: 'Token Liquidity, $',
    price: `${getTokenSymbolsString(token.symbols)} Price, $`,
  }

  const entries = Object.entries(chartTopics)
  const colors = getDistinctColors(entries.length)

  const series = Object.entries(chartTopics).map(([key, value], idx) => {
    return {
      dataKey: key,
      color: colors[idx].hex(),
      name: `${value}: `,
    }
  })

  return (
    <ResponsiveContainer width="100%" height="100%" className={styles.chart}>
      <LineChart
        data={data}
        margin={{
          top: 0,
          right: 0,
          left: 0,
          bottom: 9,
        }}>
        <XAxis
          dataKey="timestamp"
          tickFormatter={(value: number) => getDate(value * 1000, { year: undefined })}
          minTickGap={32}
          interval="preserveStartEnd"
          stroke="var(--color-text-comment)"
        />
        {series.map((item) => (
          <YAxis hide key={item.dataKey} yAxisId={item.dataKey} />
        ))}
        {series.map((item) => (
          <Line
            dot={false}
            key={item.dataKey}
            type="monotone"
            dataKey={item.dataKey}
            stroke={item.color}
            name={item.name}
            yAxisId={item.dataKey}
            strokeWidth={2}
          />
        ))}

        <Tooltip
          wrapperClassName={styles.tooltip}
          labelClassName={styles.tooltipLabel}
          separator=""
          filterNull
          formatter={(value: number) => formatNumber(value)}
          labelFormatter={(value: number) => getDate(value * 1000)}
          allowEscapeViewBox={{ x: false, y: true }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
