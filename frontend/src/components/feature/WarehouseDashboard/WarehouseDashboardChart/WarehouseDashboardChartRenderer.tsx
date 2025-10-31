'use client'

import { FC, Fragment, ReactNode } from 'react'

import clsx from 'clsx'
import get from 'lodash/get'
import {
  Area,
  Bar,
  Brush,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  TooltipContentProps,
  XAxis,
  XAxisProps,
  YAxis,
  YAxisProps,
} from 'recharts'
import { CurveType } from 'recharts/types/shape/Curve'

import Message from '@/components/ui/Message'
import Show from '@/components/ui/Show'
import { getAsArray } from '@/utils'
import { formatAutoDetect } from '@/utils/format'

import styles from './WarehouseDashboardChart.module.scss'

export type ChartData = Record<string, unknown>
export type ChartSeries = {
  type?: string
  key: string
  name?: string
  curveType?: CurveType
  color?: string
  fill?: string
  stroke?: string
  formatter?: (value: unknown) => string
  yAxis?: YAxisProps
  icon?: ReactNode
  prefix?: string
  suffix?: string
  stackId?: string
  isInZoom?: boolean
}

type ChartOptions = {
  tooltip?: {
    titleFormatter?: (value: unknown) => string
  }
  axis?: {
    y?: YAxisProps
    x?: XAxisProps & { dataKey: string }
  }
  layout?: 'vertical' | 'horizontal'
  zoom?: boolean
  isAnimated?: boolean
}

type WarehouseDashboardChartRendererProps = {
  className?: string
  data?: ChartData[]
  series?: ChartSeries | ChartSeries[]
  options?: ChartOptions
  isLoading?: boolean
}

const tickFormatter = (value: string): string => formatAutoDetect(value)

export const WarehouseDashboardChartRenderer: FC<WarehouseDashboardChartRendererProps> = ({
  data,
  series,
  options,
  className,
  isLoading,
}) => {
  const seriesArr = getAsArray(series)

  const isEmptyBrush = !options?.zoom || !seriesArr.find((set) => set.isInZoom)

  const yAxises = seriesArr.reduce<YAxisProps[]>((acc, curr) => {
    if (acc.find((item) => item.id === curr.yAxis?.id)) {
      return acc
    }

    acc.push({
      ...curr.yAxis,
      id: curr.yAxis?.id || '',
      orientation: curr.yAxis?.orientation || 'left',
      type: curr.yAxis?.type || 'number',
      tickFormatter: curr.yAxis?.tickFormatter ?? curr.formatter,
    })

    return acc
  }, [])

  const isOnlyScatterChart = !!seriesArr.filter((serie) => serie.type === 'scatter')?.length
  const TypedChart = isOnlyScatterChart ? ScatterChart : ComposedChart

  const renderTooltip = (props: TooltipContentProps<string | number, string>) => {
    const { active, payload } = props

    if (!active || !payload?.length) {
      return null
    }

    return (
      <div className={styles.tooltip}>
        <strong className={styles.tooltipLabel}>
          {(options?.axis?.x?.tickFormatter ?? formatAutoDetect)(
            get(payload[0].payload, options?.axis?.x?.dataKey ?? ''),
            0
          )}
        </strong>
        <div className={styles.tooltipBody}>
          <ul className={styles.tooltipList}>
            {payload.map((item, idx) => {
              const serie = seriesArr.find((serie) => serie.key === item.dataKey)
              if (!serie) {
                return null
              }

              const name = serie?.name ?? serie?.key
              const value = get(item.payload, serie?.key)

              return (
                <li key={idx} className={styles.tooltipItem} style={{ color: serie.color }}>
                  <div className={styles.tooltipEntry}>
                    <strong className={styles.tooltipEntryName}>{formatAutoDetect(name)}</strong>{' '}
                    <span className={styles.tooltipEntryValue}>
                      {(serie?.formatter ?? serie.yAxis?.tickFormatter ?? formatAutoDetect)(
                        value,
                        idx
                      )}
                    </span>
                  </div>
                </li>
              )
            })}
          </ul>
        </div>
      </div>
    )
  }

  return (
    <div className={clsx(styles.container, className)}>
      {isLoading && <Message type="info" text="Loading data..." />}

      {!!series && !!data && (
        <ResponsiveContainer className={styles.chart} debounce={1000}>
          <TypedChart
            data={data}
            margin={{ left: 0, right: 0, top: 0, bottom: 0 }}
            layout={options?.layout || 'horizontal'}>
            <XAxis
              fontFamily="inherit"
              fontSize={10}
              height={24}
              tickLine={false}
              axisLine={false}
              // allowDuplicatedCategory issue, so use it only when necessary
              // https://github.com/recharts/recharts/issues/2348
              allowDuplicatedCategory={!isOnlyScatterChart}
              {...options?.axis?.x}
              type={options?.axis?.x?.type || 'category'}
              minTickGap={32}
              interval="preserveStartEnd"
            />

            {yAxises.map((yAxis) => {
              return (
                <YAxis
                  key={yAxis.id}
                  fontFamily="inherit"
                  fontSize={10}
                  tickLine={false}
                  axisLine={false}
                  // allowDuplicatedCategory issue, so use it only when necessary
                  // https://github.com/recharts/recharts/issues/2348
                  allowDuplicatedCategory={!isOnlyScatterChart}
                  {...options?.axis?.y}
                  {...yAxis}
                  type={yAxis.type}
                  yAxisId={yAxis.id}
                  tickFormatter={
                    yAxis.tickFormatter ?? options?.axis?.y?.tickFormatter ?? tickFormatter
                  }
                  orientation={yAxis.orientation}
                  scale="auto"
                />
              )
            })}

            {renderSeries(seriesArr, false)}

            <Tooltip allowEscapeViewBox={{ x: false, y: true }} content={renderTooltip} />

            {options?.zoom && !isOnlyScatterChart && (
              <Brush
                travellerWidth={8}
                traveller={<CommonChartTraveller />}
                fontFamily="inherit"
                fontSize={10}
                height={isEmptyBrush ? 24 : 48}
                dataKey={options?.axis?.x?.dataKey}
                type={options?.axis?.x?.type}
                className={styles.zoom}
                tickFormatter={options?.axis?.x?.tickFormatter}>
                <Show if={!isEmptyBrush}>
                  <ComposedChart data={data} layout={options?.layout || 'horizontal'}>
                    {renderSeries(seriesArr, true)}
                  </ComposedChart>
                </Show>
              </Brush>
            )}
          </TypedChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}

const CommonChartTraveller: FC<{
  x?: number
  y?: number
  width?: number
  height?: number
}> = ({ x = 0, y = 0, width = 8, height = 16 }) => {
  return (
    <>
      <rect className="rect" x={x} y={y} width={width} height={height} />
      <path className="arrow" d={`M${x + 2} ${y + height / 2 - 3}v6l4-3-4-3Z`} />
    </>
  )
}

const renderSeries = (series: ChartSeries[], isInBrush?: boolean) => {
  return (
    <>
      {series.map((set, idx) => {
        if (isInBrush && !set.isInZoom) {
          return null
        }

        const type = set.type || 'area'
        const key = `${type}-${idx}`

        const commonProps = {
          dataKey: set.key,
          fill: set.fill ?? set.color,
          stroke: set.stroke ?? set.color,
          strokeWidth: 2,
          name: set.name,
          stackId: set?.stackId,
          yAxisId: set.yAxis?.id,
        }

        switch (type) {
          case 'scatter': {
            return <Scatter key={key} {...commonProps} strokeWidth={0} />
          }

          case 'area': {
            const fill = set.fill ?? set.color

            return (
              <Fragment key={key}>
                {!!fill && (
                  <defs>
                    <linearGradient id={`fill-${key}`} x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor={fill} stopOpacity={0.3} />
                      <stop offset="100%" stopColor={fill} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                )}
                <Area
                  type={set.curveType || 'monotone'}
                  {...commonProps}
                  fill={fill ? `url(#fill-${key})` : 'transparent'}
                />
              </Fragment>
            )
          }

          case 'column':
          case 'bar': {
            const fill = set.fill ?? set.color

            return <Bar key={key} {...commonProps} fill={fill} />
          }

          default: {
            return (
              <Line key={key} type={set.curveType || 'monotone'} dot={false} {...commonProps} />
            )
          }
        }
      })}
    </>
  )
}
