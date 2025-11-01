'use client'

import { FC, useState } from 'react'

import clsx from 'clsx'

import Message from '@/components/ui/Message'
import TimerCountdown from '@/components/ui/TimerCountdown'
import { useQueryResult } from '@/hooks/warehouse/useQueryResult'
import IconRefresh from '@/images/icons/time-ago.svg'
import { TWarehouseQueryResponse, TWarehouseVisualization } from '@/services/warehouse-redash/types'

import { useQueryResponse } from '../../../../hooks/warehouse/useQueryResponse'
import WarehouseDashboardChart from '../WarehouseDashboardChart'
import { WarehouseDashboardWidgetCounter } from './WarehouseDashboardWidgetCounter'
import { WarehouseDashboardWidgetTable } from './WarehouseDashboardWidgetTable'

import styles from './WarehouseDashboardWidget.module.scss'

type WarehouseDashboardWidgetRendererProps = {
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
  isDefault?: boolean
  allowUpdate?: boolean
}

export const WarehouseDashboardWidgetRenderer: FC<WarehouseDashboardWidgetRendererProps> = ({
  visualization,
  queryResponse,
  params,
  isDefault,
  allowUpdate,
}) => {
  const [isRefetch, setIsRefetch] = useState(!isDefault || Boolean(queryResponse?.job))

  const {
    isError: isErrorLatestQueryResult,
    isFetching: isFetchingLatestQueryResult,
    data: latestQueryResponse,
  } = useQueryResult(visualization.query.latest_query_data_id || 0, {
    refetchOnWindowFocus: false,
    enabled: !!visualization.query.latest_query_data_id,
  })

  const { isError, isFetching, isActiveJob, job, result, refetch } = useQueryResponse({
    queryId: visualization.query.id,
    initialData: queryResponse,
    params,
    maxAge: 60,
    enabled: !visualization.query.latest_query_data_id && isRefetch,
  })

  const queryResult = latestQueryResponse?.query_result || result

  const isProcessing = isFetchingLatestQueryResult || isFetching || isActiveJob

  if (
    !isProcessing &&
    (isErrorLatestQueryResult || isError || job?.error || (job?.status ?? 0) > 3)
  ) {
    return (
      <div className={styles.body}>
        <div className={styles.empty}>
          <Message type="danger">Data can&apos;t be processed at the moment.</Message>
        </div>
      </div>
    )
  }

  if (!isProcessing && !job && queryResult?.data?.rows?.length === 0) {
    return (
      <div className={styles.body}>
        <div className={styles.empty}>
          <Message type="info">Empty data</Message>
        </div>
      </div>
    )
  }

  const handleRefetch = () => {
    setIsRefetch(true)
    refetch()
  }

  const footerContent = allowUpdate ? (
    <div className={styles.footer}>
      <button
        className={clsx(styles.refresh, { [styles.loading]: isProcessing })}
        onClick={handleRefetch}
        disabled={isProcessing}>
        <IconRefresh className={styles.icon} />

        {isFetching && !isActiveJob && 'Requesting...'}
        {isActiveJob && 'Calculating...'}
        {!isProcessing && !!queryResult?.retrieved_at && (
          <TimerCountdown
            className={styles.timer}
            timestamp={queryResult?.retrieved_at}
            isCompact
            prefix="Updated "
            suffix=" ago"
          />
        )}
      </button>
    </div>
  ) : null

  if (visualization?.type === 'COUNTER') {
    return (
      <>
        <div className={styles.body}>
          <WarehouseDashboardWidgetCounter
            isLoading={isProcessing}
            value={
              `${
                queryResult?.data?.rows?.[
                  (Math.max(visualization.options.rowNumber ?? 0, 0) || 1) - 1
                ]?.[visualization.options.counterColName || '']
              }` || null
            }
            unit={visualization.options.stringSuffix}
            subtitle={
              visualization.options.counterLabel ??
              `${
                queryResult?.data?.rows?.[
                  (Math.max(visualization.options.targetRowNumber ?? 0, 0) || 1) - 1
                ]?.[visualization.options.targetColName || '']
              }`
            }
          />
        </div>
        {footerContent}
      </>
    )
  }

  const nameType = visualization?.name?.toLowerCase().split('_')

  if (nameType?.[1] === 'treemap') {
    return (
      <>
        <div className={styles.body}>
          <WarehouseDashboardChart
            className={styles.chart}
            isLoading={isProcessing}
            type={nameType?.[1]}
            visualization={visualization}
            data={queryResult?.data}
          />
        </div>
        {footerContent}
      </>
    )
  }

  if (visualization?.type === 'CHART') {
    return (
      <>
        <div className={styles.body}>
          <WarehouseDashboardChart
            className={styles.chart}
            isLoading={isProcessing}
            type={visualization.options?.globalSeriesType || 'unknown'}
            visualization={visualization}
            data={queryResult?.data}
          />
        </div>
        {footerContent}
      </>
    )
  }

  if (visualization?.type === 'TABLE') {
    return (
      <>
        <div className={styles.body}>
          <WarehouseDashboardWidgetTable
            options={visualization.options}
            data={queryResult?.data}
            isLoading={isProcessing}
          />
        </div>
        {footerContent}
      </>
    )
  }

  if (visualization?.type) {
    return (
      <div className={styles.body}>
        <Message type="danger">
          Visualization type {visualization.type} is not supported yet
        </Message>
      </div>
    )
  }

  return null
}
