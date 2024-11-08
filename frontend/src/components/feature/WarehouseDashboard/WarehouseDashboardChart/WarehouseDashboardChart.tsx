import { CSSProperties, FC } from 'react'

import clsx from 'clsx'
import { scaleSymlog } from 'd3-scale'
import { groupBy } from 'lodash'
import { AxisDomain } from 'recharts/types/util/types'

import { TWarehouseQueryResultData, TWarehouseVisualization } from '@/actions/warehouse/types'
import Loader from '@/components/atoms/Loader'
import Message from '@/components/ui/Message'
import { DEFAULT_COLOR_MAIN, getDistinctColors } from '@/utils/colors'
import { formatAutoDetect, formatByType } from '@/utils/format'
import { formatNumber } from '@/utils/numbers'

import { WarehouseDashboardChartHeatmap } from './WarehouseDashboardChartHeatmap'
import { WarehouseDashboardChartPie } from './WarehouseDashboardChartPie'
import { ChartSeries, WarehouseDashboardChartRenderer } from './WarehouseDashboardChartRenderer'

import styles from './WarehouseDashboardChart.module.scss'

const SUPPORTED_CHARTS = ['line', 'area', 'column', 'bar', 'pie', 'heatmap', 'scatter']

const tickFormatter = (value: string) => formatAutoDetect(value, { notation: 'compact' })

export const WarehouseDashboardChart: FC<{
  className?: string
  type: string
  data?: TWarehouseQueryResultData
  visualization: TWarehouseVisualization
  isLoading?: boolean
}> = ({ type, data, visualization, isLoading, className }) => {
  if (!SUPPORTED_CHARTS.includes(type)) {
    return <Message type="danger" text="This chart type is currently not supported" />
  }

  if (isLoading) {
    return (
      <div className={clsx(styles.container, className)}>
        <Loader className={styles.suspense} />
      </div>
    )
  }

  if (type === 'heatmap') {
    const mapping = Object.fromEntries(
      Object.entries(visualization.options.columnMapping || {}).map(([key, value]) => [value, key])
    )

    const tooltipName = (visualization.options.seriesOptions || {})[mapping.y]?.name

    return (
      <div
        className={clsx(
          styles.heatmap,
          { [styles.loading]: isLoading },
          { [styles.empty]: !data?.rows?.length }
        )}>
        <div className={styles.wrapper}>
          <WarehouseDashboardChartHeatmap
            className={styles.heatmapChart}
            data={data?.rows}
            keys={{ x: mapping.x, y: mapping.y, val: mapping.zVal }}
            tickXFormatter={tickFormatter}
            tooltipFormat={({ x, y, value }) => {
              return `${tooltipName ? `${tooltipName} on ` : ''} ${x} ${y}: ${formatNumber(value)}`
            }}
          />
        </div>
      </div>
    )
  }

  if (type === 'pie') {
    const mapping = Object.fromEntries(
      Object.entries(visualization.options.columnMapping || {}).map(([key, value]) => [value, key])
    )

    const colors = getDistinctColors(Math.max(data?.rows?.length ?? 0, 1)).map((item) => item.hex())

    return (
      <div
        className={clsx(
          styles.pie,
          { [styles.loading]: isLoading },
          { [styles.empty]: !data?.rows?.length },
          className
        )}>
        <WarehouseDashboardChartPie
          className={styles.pieChart}
          data={data?.rows || []}
          dataKey={mapping.y}
          nameKey={mapping.x}
          colors={colors}
          formatter={(val) => formatNumber(`${val}`)}
        />

        {visualization.options?.legend?.enabled && (
          <ul className={styles.pieLegend}>
            {data?.rows.map((item, idx) => {
              return (
                <li
                  key={idx}
                  className={styles.pieEntry}
                  style={
                    {
                      '--color': colors?.length === 1 ? DEFAULT_COLOR_MAIN : colors[idx],
                    } as CSSProperties
                  }>
                  <span className={styles.caption}>{formatAutoDetect(item[mapping.x])}</span>
                </li>
              )
            })}
          </ul>
        )}
      </div>
    )
  }

  if (!['line', 'area', 'column', 'bar', 'scatter'].includes(type)) {
    return <Message type="warn">Type &quot;{type}&quot; is not implemented yet</Message>
  }

  const columnMappingEntries = Object.entries(visualization.options.columnMapping || {})

  const xKey = columnMappingEntries.find(([, value]) => value === 'x')?.[0] || 'x'

  const groupByKey = columnMappingEntries.find(([, value]) => value === 'series')?.[0] ?? '-'
  const groupedChartData = groupByKey
    ? groupBy(data?.rows ?? [], groupByKey)
    : { '-': data?.rows ?? [] }
  const groupedChartEntries = Object.entries(groupedChartData)

  const yAxisColumns = (data?.columns || [])?.filter((column) => {
    return visualization.options.columnMapping?.[column.name] === 'y'
  })

  const xAxisType = visualization.options.xAxis.type

  const yCategoryValues: Record<string, string[]> = {}

  const groupedChartDataBySeriesByXKey = groupBy(
    groupedChartEntries
      .map(([key, arr]) =>
        arr.map((item) => ({
          [key]: Object.fromEntries(
            yAxisColumns.map(({ name }) => {
              const yAxisId = visualization.options.seriesOptions?.[name]?.yAxis || 0

              if (visualization.options.yAxis[yAxisId].type === 'category') {
                if (!yCategoryValues[yAxisId]) {
                  yCategoryValues[yAxisId] = []
                }

                const valStr = item[name].toString()

                let valIdx = yCategoryValues[yAxisId]?.findIndex((item) => item === valStr)

                if (valIdx === -1) {
                  valIdx = yCategoryValues[yAxisId].push(valStr) - 1
                }

                return [name, valIdx]
              }

              return [name, item[name]]
            })
          ),
          [xKey]: item[xKey],
        }))
      )
      .flat(),
    xKey
  )

  const chartDataTransformed = Object.fromEntries(
    Object.entries(groupedChartDataBySeriesByXKey)
      .sort(([a], [b]) => (b > a ? -1 : 1) * (visualization.options.reverseX ? -1 : 1))
      .map(([key, arr]) => [key, arr.reduce((acc, item) => ({ ...acc, ...item }), {})])
  )

  const colors = getDistinctColors(groupedChartEntries.length * yAxisColumns.length)

  const dataSeries: ChartSeries[] = []

  groupedChartEntries.forEach(([groupedDataKey], setIdx) => {
    yAxisColumns.forEach((column, colIdx) => {
      const idx = (setIdx + 1) * (colIdx + 1) - 1

      const yAxisId = visualization.options.seriesOptions?.[column.name]?.yAxis || 0
      const yAxisType =
        visualization.options.yAxis[yAxisId].type === 'category' ? 'category' : 'number'
      const yAxisScale =
        visualization.options.yAxis[yAxisId].type === 'logarithmic' ? scaleSymlog() : undefined
      const yAxisDomain: AxisDomain =
        visualization.options.yAxis[yAxisId].type === 'category'
          ? ['dataMin', 'dataMax']
          : [
              visualization.options.yAxis[yAxisId].rangeMin ?? 'auto',
              visualization.options.yAxis[yAxisId].rangeMax ?? 'auto',
            ]

      const dataSet: ChartSeries = {
        key: `${groupedDataKey}.${column.name}`,
        type: visualization.options.seriesOptions?.[column.name]?.type ?? type,
        stackId: visualization.options.series?.stacking,
        formatter: (value) => {
          if (yAxisType === 'category') {
            const yCategoryValue = yCategoryValues[yAxisId]?.[Number(value)]
            return tickFormatter(`${yCategoryValue || ''}`)
          }

          return tickFormatter(`${value}`)
        },
        name:
          (groupedChartEntries.length > 1 ? groupedDataKey : null) ??
          visualization.options.seriesOptions?.[column.name]?.name ??
          column.friendly_name ??
          column.name,
        yAxis: {
          id: `yAxis${yAxisId}`,
          orientation: visualization.options.yAxis[yAxisId].opposite ? 'right' : 'left',
          type: 'number',
          scale: yAxisScale,
          domain: yAxisDomain,
          // interval: yAxisType === 'category' ? 0 : undefined,
          tickCount: yCategoryValues[yAxisId]?.length,
        },
        color:
          visualization.options.seriesOptions?.[column.name]?.color ??
          (colors.length === 1 ? DEFAULT_COLOR_MAIN : colors[idx]?.hex()),
      }

      dataSeries.push(dataSet)
    })
  })

  const chartData = Object.values(chartDataTransformed)

  return (
    <WarehouseDashboardChartRenderer
      className={className}
      series={dataSeries}
      data={chartData}
      options={{
        zoom: chartData.length > 10,
        axis: {
          x: {
            dataKey: xKey,
            axisLine: false,
            tickLine: false,
            tickFormatter: (value) => formatByType(xAxisType, value),
          },
          y: {
            axisLine: false,
            tickLine: false,
            tickFormatter,
          },
        },
      }}
    />
  )
}
