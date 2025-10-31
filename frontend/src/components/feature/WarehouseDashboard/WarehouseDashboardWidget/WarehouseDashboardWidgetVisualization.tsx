import { FC } from 'react'

import {
  TWarehouseQueryParam,
  TWarehouseQueryParamDateRange,
  TWarehouseQueryResponse,
  TWarehouseVisualization,
  TWarehouseWidgetParam,
} from '@/services/warehouse-redash/types'
import {
  generateWarehouseQueryParams,
  getDateRangeToString,
} from '@/services/warehouse-redash/utils'
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
  isDefault?: boolean
  allowUpdate?: boolean
}> = ({ visualization, params, mapping, allowUpdate }) => {
  if (!visualization?.type) {
    return null
  }

  const mappedParams: Record<string, string | undefined> = {}
  Object.values(mapping).forEach((mapped) => {
    const mapTo = mapped.mapTo || mapped.name

    mappedParams[mapTo] =
      getExactValue(params?.[mapTo]?.value) || getExactValue(mapped.value) || undefined
  })
  const requestParams = generateWarehouseQueryParams(visualization?.query, mappedParams, mapping)

  return (
    <WarehouseDashboardWidgetRenderer
      visualization={visualization}
      params={requestParams}
      allowUpdate={allowUpdate}
    />
  )
}
