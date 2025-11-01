import React, { FC } from 'react'

import { Area, AreaChart, ResponsiveContainer, XAxis, YAxis } from 'recharts'

import Loader from '@/components/atoms/Loader'
import Show from '@/components/ui/Show'
import { hashOfString } from '@/utils/strings'

import styles from './DashboardWidgetChart.module.scss'

export type DashboardWidgetChartProps = {
  isLoading?: boolean
  data: { x: string; y: number }[]
  color?: string
}

export const DashboardWidgetChart: FC<DashboardWidgetChartProps> = ({
  isLoading,
  data,
  color = 'var(--color-primary)',
}) => {
  const hash = hashOfString(color)
  return (
    <div className={styles.container}>
      <Show if={isLoading}>
        <Loader className={styles.loader} />
      </Show>
      <Show if={!isLoading && data.length}>
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{
              top: 0,
              right: 0,
              left: 0,
              bottom: 0,
            }}>
            <defs>
              <linearGradient id={`gradient-${hash}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0" stopColor={color} stopOpacity={0.4}></stop>
                <stop offset="1" stopColor={color} stopOpacity={0.0}></stop>
              </linearGradient>
            </defs>
            <XAxis
              dataKey="x"
              fontFamily="inherit"
              fontSize={12}
              height={18}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              fontFamily="inherit"
              fontSize={10}
              height={18}
              tickLine={false}
              axisLine={false}
            />
            <Area
              type="monotone"
              dataKey="y"
              stroke={color}
              fill={`url(#gradient-${hash})`}
              strokeWidth={3}
            />
          </AreaChart>
        </ResponsiveContainer>
      </Show>
    </div>
  )
}
