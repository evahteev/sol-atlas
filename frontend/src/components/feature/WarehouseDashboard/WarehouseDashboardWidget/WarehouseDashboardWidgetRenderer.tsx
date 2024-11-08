'use client'

import { FC } from 'react'

import { TWarehouseQueryResponse, TWarehouseVisualization } from '@/actions/warehouse/types'
import Message from '@/components/ui/Message'

import WarehouseDashboardChart from '../WarehouseDashboardChart'
import { useQueryResponse } from '../hooks'
import { WarehouseDashboardWidgetCounter } from './WarehouseDashboardWidgetCounter'
import { WarehouseDashboardWidgetTable } from './WarehouseDashboardWidgetTable'

import styles from './WarehouseDashboardWidget.module.scss'

export const WarehouseDashboardWidgetRenderer: FC<{
  visualization: TWarehouseVisualization
  queryResponse?: TWarehouseQueryResponse
  params?:
    | Record<
        string,
        | string
        | number
        | null
        | {
            start: string | null
            end: string | null
          }
      >
    | undefined
}> = ({ visualization, queryResponse, params }) => {
  const { isError, isFetching, isActiveJob, job, result } = useQueryResponse({
    queryId: visualization.query.id,
    queryResponse,
    params,
  })

  const isProcessing = isFetching || isActiveJob

  if (!isProcessing && (isError || job?.error || (job?.status ?? 0) > 3)) {
    return (
      <div className={styles.empty}>
        <Message type="danger">Data can&apos;t be processed at the moment.</Message>
      </div>
    )
  }

  if (!isProcessing && !job && result?.data?.rows?.length === 0) {
    return (
      <div className={styles.empty}>
        <Message type="info">Empty data</Message>
      </div>
    )
  }

  if (visualization?.type === 'COUNTER') {
    return (
      <WarehouseDashboardWidgetCounter
        isLoading={isProcessing}
        value={
          result?.data?.rows?.[(Math.max(visualization.options.rowNumber ?? 0, 0) || 1) - 1]?.[
            visualization.options.counterColName || ''
          ] || null
        }
        unit={visualization.options.stringSuffix}
        subtitle={visualization.options.counterLabel}
      />
    )
  }

  if (visualization?.type === 'CHART') {
    return (
      <WarehouseDashboardChart
        className={styles.chart}
        isLoading={isProcessing}
        type={visualization.options?.globalSeriesType || 'unknown'}
        visualization={visualization}
        data={result?.data}
      />
    )
  }

  if (visualization?.type === 'TABLE') {
    return (
      <WarehouseDashboardWidgetTable
        options={visualization.options}
        data={result?.data}
        isLoading={isProcessing}
      />
    )
  }

  if (visualization?.type) {
    return (
      <Message type="danger">Visualization type {visualization.type} is not supported yet</Message>
    )
  }

  return null
}
