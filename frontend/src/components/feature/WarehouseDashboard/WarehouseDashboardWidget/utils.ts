import { TWarehouseVisualization } from '@/actions/warehouse/types'
import { generateWarehouseQueryParams } from '@/actions/warehouse/utils'
import { DEFAULT_DATE_RANGE, DYNAMIC_DATE_PREFIX } from '@/utils/dates'

export const QUERY_DEFAULT_DATERANGE = `${DYNAMIC_DATE_PREFIX}${DEFAULT_DATE_RANGE}`

export const getVisualizationQueryParams = (
  visualization: TWarehouseVisualization,
  params: Record<string, string | undefined>
) =>
  visualization?.query
    ? generateWarehouseQueryParams(visualization?.query, params ?? {})
    : undefined
