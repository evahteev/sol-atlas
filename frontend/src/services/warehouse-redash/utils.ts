import uniqBy from 'lodash/uniqBy'

import {
  DEFAULT_DATE_RANGE,
  DYNAMIC_DATE_PREFIX,
  getDynamicDateRangePeriod,
} from '../../utils/dates'
import { AppFetchProps } from './fetch'
import {
  TWarehouseDashboard,
  TWarehouseQuery,
  TWarehouseQueryParam,
  TWarehouseQueryParamDateRange,
  TWarehouseWidgetParam,
} from './types'

export async function warehouseFetch(props: AppFetchProps) {
  const nextjsServerOrigin = process.env.NEXTJS_SERVER_LOCAL_ORIGIN || 'https://localhost:3000'
  return fetch(`${typeof window === 'undefined' ? nextjsServerOrigin : ''}/api/warehouse-redash`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(props),
  })
}

export const getDateRangeToString = (value: TWarehouseQueryParamDateRange): string => {
  if (typeof value === 'string') {
    return value
  }

  if (value?.start || value?.end) {
    return `${value?.start || ''}--${value?.end || ''}`
  }

  return ''
}

export const getDateRangeFromValue = (
  value: TWarehouseQueryParamDateRange,
  forceProcessDynamicPeriod = true
): TWarehouseQueryParamDateRange => {
  if (typeof value !== 'string' && (value?.start || value?.end)) {
    return { start: value.start, end: value.end }
  }

  const dateRange = `${value}`.match(/((\d{4}-\d{2}-\d{2})|())--((\d{4}-\d{2}-\d{2})|())/)

  if (dateRange) {
    return {
      start: dateRange[1],
      end: dateRange[4],
    }
  }

  return forceProcessDynamicPeriod
    ? getDynamicDateRangePeriod(
        `${value || `${DYNAMIC_DATE_PREFIX}${DEFAULT_DATE_RANGE}`}`,
        'datetime-range-with-seconds'
      )
    : value
}

export const getWarehouseDashboardParams = (
  dashboard: TWarehouseDashboard,
  globalParams?: Record<string, string | null | undefined>,
  forceProcessDynamicPeriod = false
): Record<string, TWarehouseQueryParam> => {
  const params = dashboard.widgets
    ?.map((widget) =>
      (widget.visualization?.query?.options?.parameters ?? []).map((queryParam) => {
        const mapped = Object.values(widget.options.parameterMappings ?? {}).find(
          (mapped) => queryParam.name === mapped.name
        ) ?? {
          name: queryParam.name,
          mapTo: queryParam.name,
          title: queryParam.name,
          type: 'widget-level',
          value: queryParam.value,
        }

        const exactValue =
          mapped?.value ??
          globalParams?.[mapped.mapTo] ??
          globalParams?.[mapped.name] ??
          queryParam?.value ??
          null

        return {
          name: mapped?.mapTo || mapped?.name || queryParam.name,
          title: mapped?.title || mapped?.name || queryParam?.title || queryParam?.name || '',
          type: queryParam?.type || 'text',
          value: ['date-range', 'datetime-range', 'datetime-range-with-seconds'].includes(
            queryParam?.type ?? ''
          )
            ? getDateRangeFromValue(exactValue, forceProcessDynamicPeriod)
            : exactValue,
          queryId: queryParam?.type === 'query' ? queryParam?.queryId : undefined,
          level: mapped?.type,
        } as TWarehouseQueryParam
      })
    )
    ?.flat()
  // .filter((item) => item.level === 'dashboard-level')

  return Object.fromEntries(uniqBy(params, 'name').map((param) => [param.name, param]))
}

const getParamValueByType = (
  value: string | null | TWarehouseQueryParamDateRange,
  type: string
) => {
  if (['date-range', 'datetime-range', 'datetime-range-with-seconds'].includes(type)) {
    return getDateRangeFromValue(value)
  }

  return value
}

export const generateWarehouseQueryParams = (
  query?: TWarehouseQuery,
  params?: Record<string, string | undefined>,
  mapping?: Record<string, TWarehouseWidgetParam>
):
  | Record<string, string | number | null | { start: string | null; end: string | null }>
  | undefined => {
  if (!query) {
    return undefined
  }

  const {
    options: { parameters: queryParameters },
  } = query

  return Object.fromEntries(
    queryParameters?.map((param) => {
      const mapItem = mapping?.[param.name]

      return [
        mapItem?.name || param.name,
        getParamValueByType(
          params?.[mapItem?.mapTo || mapItem?.name || param.name] || param?.value || null,
          param.type
        ),
      ]
    }) || []
  )
}
