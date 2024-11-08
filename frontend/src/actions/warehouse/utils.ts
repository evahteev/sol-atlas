import { uniqBy } from 'lodash'

import {
  DEFAULT_DATE_RANGE,
  DYNAMIC_DATE_PREFIX,
  getDynamicDateRangePeriod,
} from '../../utils/dates'
import { AppFetchProps, appFetch } from './fetch'
import {
  TWarehouseDashboard,
  TWarehouseQuery,
  TWarehouseQueryParam,
  TWarehouseQueryParamDateRange,
} from './types'

export async function warehouseFetch(props: AppFetchProps) {
  return appFetch({
    url: `${process.env.WAREHOUSE_API_HOST}/api${props.url}`,
    method: props.data ? 'POST' : 'GET',
    headers: {
      'Content-Type': 'application/json',
      Authorization: process.env.WAREHOUSE_API_KEY ?? '',
    },
    data: props.data,
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
  return Object.fromEntries(
    uniqBy(
      dashboard.widgets
        ?.map((widget) =>
          Object.values(widget.options.parameterMappings ?? {}).map((mapped) => {
            const queryParam = widget.visualization.query.options.parameters?.find(
              (param) => param.name === mapped.name
            )

            const exactValue =
              globalParams?.[mapped.name] ?? mapped.value ?? queryParam?.value ?? null

            return {
              name: mapped.name,
              title: mapped.title || mapped.name || queryParam?.title || queryParam?.name || '',
              type: queryParam?.type || 'text',
              value: ['date-range', 'datetime-range', 'datetime-range-with-seconds'].includes(
                queryParam?.type ?? ''
              )
                ? getDateRangeFromValue(exactValue, forceProcessDynamicPeriod)
                : exactValue,
              queryId: queryParam?.type === 'query' ? queryParam?.queryId : undefined,
              level: mapped.type,
            } as TWarehouseQueryParam
          })
        )
        ?.flat() ?? [],
      'name'
    ).map((param) => [param.name, param])
  )
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
  globalParams?: Record<string, string | undefined>
):
  | Record<string, string | number | null | { start: string | null; end: string | null }>
  | undefined => {
  if (!query) {
    return undefined
  }

  const {
    options: { parameters: queryParameters },
  } = query

  const params =
    queryParameters?.map((param) => {
      return [
        param.name,
        getParamValueByType(globalParams?.[param.name] || param.value, param.type),
      ]
    }) || []

  return Object.fromEntries(params)
}
