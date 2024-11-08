import { FC } from 'react'

import { getWarehouseQueryResponse } from '@/actions/warehouse'
import {
  TWarehouseQueryParam,
  TWarehouseQueryParamDateRange,
  TWarehouseQueryResponse,
  TWarehouseVisualization,
  TWarehouseWidgetParam,
} from '@/actions/warehouse/types'
import { generateWarehouseQueryParams, getDateRangeToString } from '@/actions/warehouse/utils'
import { isTypeObject } from '@/utils'

import { WarehouseDashboardWidgetRenderer } from './WarehouseDashboardWidgetRenderer'

const getExactValue = (
  value?: string | TWarehouseQueryParamDateRange | null
): string | undefined => {
  if (!value) {
    return undefined
  }

  if (typeof value === 'string') {
    return value
  }

  if (isTypeObject(value) && (value.start || value.end)) {
    return getDateRangeToString(value)
  }

  return undefined
}

export const WarehouseDashboardWidgetVisualization: FC<{
  visualization: TWarehouseVisualization
  queryResponse?: TWarehouseQueryResponse
  params?: Record<string, TWarehouseQueryParam>
  mapping: Record<string, TWarehouseWidgetParam>
}> = async ({ visualization, params, mapping }) => {
  if (!visualization?.type) {
    return null
  }

  const mappedParams: Record<string, string | undefined> = {}
  Object.values(mapping).forEach((mapped) => {
    mappedParams[mapped.name] =
      getExactValue(params?.[mapped.name].value) || getExactValue(mapped.value) || undefined
  })
  const requestParams = generateWarehouseQueryParams(visualization?.query, mappedParams)
  const queryResponse = await getWarehouseQueryResponse(visualization.query.id, requestParams)

  return (
    <WarehouseDashboardWidgetRenderer
      visualization={visualization}
      params={requestParams}
      queryResponse={queryResponse ?? {}}
    />
  )
}
