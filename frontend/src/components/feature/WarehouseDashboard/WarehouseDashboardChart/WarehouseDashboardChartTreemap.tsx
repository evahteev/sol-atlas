import { FC } from 'react'

import clsx from 'clsx'
import { ResponsiveContainer, Treemap } from 'recharts'

import { TWarehouseVisualization } from '@/services/warehouse-redash/types'
import { getDistinctColors } from '@/utils/colors'
import { formatNumber } from '@/utils/numbers'

import styles from './WarehouseDashboardChartTreemap.module.scss'

export type HeatmapChartEntry = Record<string, unknown>
export type HeatmapChartData = HeatmapChartEntry[]
export type HeatmapChartProps = {
  data?: HeatmapChartData
  className?: string
  visualization: TWarehouseVisualization
  tickXFormatter?: (value: string) => string
  tickYFormatter?: (value: string) => string
  tooltipFormat?: (props: { x: string; y: string; value: string | number }) => string
}

export const WarehouseDashboardChartTreemap: FC<HeatmapChartProps> = ({
  data,
  className,
  visualization,
}) => {
  if (!data) {
    return null
  }

  const columns = Object.entries(visualization.options.columns || {})
  const colName = columns?.find(([, col]) => [col.name, col.title].includes('name'))?.[1]?.name
  const colValue = columns?.find(([, col]) => [col.name, col.title].includes('value'))?.[1]?.name

  const colors = getDistinctColors(data.length)

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const CustomizedContent = (props: any) => {
    const { depth, suffix, prefix, index, x, y, width, height } = props

    if (depth === 0) {
      return null
    }

    const name = props[colName || 'name']
    const value = props[colValue || 'value']

    return (
      <svg x={x + 2} y={y + 2} width={width - 4} height={height - 4}>
        <rect
          width="100%"
          height="100%"
          style={{
            fill: `${colors?.[index].alpha(0.25).hex() || 'var(--color-dark-50)'}`,
          }}
        />
        <text
          overflow="hidden"
          x={8}
          y={8 + 14}
          textAnchor="start"
          fill="var(--color-text-main)"
          fontSize={10}>
          {prefix}
          {name}
          {suffix}
        </text>
        <text
          overflow="hidden"
          x={8}
          y={8 + 14 + 4 + 16}
          width={16}
          textAnchor="start"
          fill="var(--color-text-main)"
          fontSize={14}
          font-weight="bold">
          {formatNumber(value)}
        </text>
      </svg>
    )
  }

  return (
    <div className={clsx(styles.container, className)}>
      <ResponsiveContainer className={styles.chart} debounce={1000}>
        <Treemap
          isAnimationActive={false}
          width={400}
          height={200}
          data={data}
          dataKey={colValue}
          nameKey={colName}
          aspectRatio={4 / 3}
          className={styles.treemap}
          content={<CustomizedContent />}
        />
      </ResponsiveContainer>
    </div>
  )
}
