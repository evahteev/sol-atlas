export type TWarehouseWidgetParam = {
  name: string
  type: string
  mapTo: string
  value: string | TWarehouseQueryParamDateRange | null
  title: string
}

export type TWarehouseWidgetOptions = {
  isHidden: boolean
  parameterMappings?: Record<string, TWarehouseWidgetParam>
  text: string
  position: {
    autoHeight: boolean
    sizeX: number
    sizeY: number
    minSizeX: number
    maxSizeX: number
    minSizeY: number
    maxSizeY: number
    col: number
    row: number
  }
}

export type TWarehouseQueryParamDateRange =
  | string
  | null
  | { start: string | null; end: string | null }

export type TWarehouseQueryParam = {
  title: string
  name: string
  level?: string
} & (
  | {
      type: 'date-range' | 'datetime-range' | 'datetime-range-with-seconds'
      value: TWarehouseQueryParamDateRange
    }
  | { type: 'text'; value: string | null }
  | { type: 'query'; value: string | null; queryId: number }
)

export type TWarehouseQuery = {
  id: number
  name: string
  description: string
  options: {
    parameters?: TWarehouseQueryParam[]
  }
}

type TWarehouseTableColumn = {
  visible?: boolean
  order?: number
  title?: string
  name: string
  type: 'integer' | 'string'
}

export type TWarehouseVisualizationOptions = unknown & {
  globalSeriesType?: string
  columnMapping?: Record<string, string>
  counterLabel?: string
  counterColName?: string
  rowNumber?: 1
  series?: {
    stacking?: string
  }
  seriesOptions?: Record<string, { name?: string; type?: string; color?: string; yAxis: number }>
  legend?: {
    enabled?: boolean
  }
  swappedAxes?: boolean
  columns?: TWarehouseTableColumn[]
  stringSuffix?: string
  yAxis: { type: string; opposite?: boolean; rangeMax: number | null; rangeMin: number | null }[]
  xAxis: { type: string }
  reverseX?: boolean
}

export type TWarehouseVisualization = {
  type: string
  name: string
  description: string
  query: TWarehouseQuery
  options: TWarehouseVisualizationOptions
}

export type TWarehouseWidget = {
  id: number
  options: TWarehouseWidgetOptions
  visualization: TWarehouseVisualization
  text: string
}

export type TWarehouseQueryResultData = {
  columns: Array<{
    name: string
    friendly_name: string
    type: string
  }>
  rows: Array<Record<string, number | string>>
}

export type TWarehouseQueryResult = {
  data: TWarehouseQueryResultData
  retrieved_at: string
  id: number
}

export type TWarehouseJob = {
  id: string
  status: number
  error: string
  result: null
  query_result_id: number | null
}

export type TWarehouseQueryResponse = {
  query_result?: TWarehouseQueryResult
  job?: TWarehouseJob
}

export type TWarehouseDashboardTag = { count: number; name: string }

export type TWarehouseDashboard = {
  id: number
  name: string
  slug: string
  dashboard_filters_enabled?: boolean
  widgets?: TWarehouseWidget[]
  is_draft: boolean
  is_archived: boolean
  public_url: string
  tags: string[]
  text: string
  visualization_types?: Array<{
    [type: string]: {
      sizeX: number
      sizeY: number
      col: number
      row: number
      globalSeriesType: string
    }
  }>

  user: {
    id: number
    name: string
    email: string
    profile_image_url: string
  }

  updated_at: string
  created_at: string
}
