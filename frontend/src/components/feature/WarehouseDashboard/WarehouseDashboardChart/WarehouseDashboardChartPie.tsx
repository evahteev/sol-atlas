import { FC } from 'react'

import clsx from 'clsx'
import {
  Cell,
  PieChart as Chart,
  Pie,
  PieLabelRenderProps,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import uniqolor from 'uniqolor'

import { formatAutoDetect } from '@/utils/format'
import { formatNumber } from '@/utils/numbers'

import styles from './WarehouseDashboardChart.module.scss'

export type PieChartProps = {
  data: Record<string, unknown>[]
  className?: string
  dataKey: string
  nameKey: string
  formatter: (value: unknown, idx: number) => string
  colors?: string[]
}

export const WarehouseDashboardChartPie: FC<PieChartProps> = ({
  data,
  className,
  dataKey,
  nameKey,
  colors,
  formatter,
}) => {
  return (
    <ResponsiveContainer width="100%" height="100%" className={clsx(styles.container, className)}>
      <Chart className={styles.chart}>
        <Tooltip
          wrapperClassName={styles.tooltip}
          labelClassName={styles.tooltipLabel}
          separator=""
          filterNull
          formatter={formatter}
          allowEscapeViewBox={{ x: true, y: true }}
        />

        <Pie
          className={clsx(styles.pie)}
          data={data}
          dataKey={dataKey}
          innerRadius="40%"
          cx="50%"
          cy="50%"
          label={({ percent }: PieLabelRenderProps) =>
            `${formatNumber(((percent as number) || 0) * 100)}%`
          }
          labelLine
          fontSize={10}>
          {data.map((el, idx) => {
            const color = colors?.[idx] ?? uniqolor(`${el[nameKey]}${idx}`).color
            return (
              <Cell
                name={formatAutoDetect(`${el[nameKey]}`)}
                color={color}
                className={styles.cell}
                fill={color}
                key={`${el[nameKey]}`}
                stroke="transparent"
              />
            )
          })}
        </Pie>
      </Chart>
    </ResponsiveContainer>
  )
}
