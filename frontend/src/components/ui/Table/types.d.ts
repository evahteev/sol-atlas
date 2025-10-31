import { ReactNode } from 'react'

import { UrlObject } from 'url'

export type TableColumnProps<T, V = Record<string, unknown>> = {
  render?: (props: { data: T; placeholder?: ReactNode; idx?: number; vars?: V }) => ReactNode
  accessor?: string
  title?: ReactNode
  tooltip?: string
  type?: 'number' | 'text' | 'center'
  modifier?: string
  placeholder?: ReactNode
  className?: string
}

export type TableRowHref<T> =
  | (string | UrlObject | null)
  | ((data?: T, idx?: number) => string | UrlObject | null)

export type TableRowProps = Record<string, unknown>

export type TableProps<T, V = Record<string, unknown>> = {
  title?: ReactNode
  columns: TableColumnProps<T, V>[]
  data: T[]
  className?: string
  classNameTable?: string
  classNameTHead?: string
  classNameTBody?: string
  classNameTCell?: string
  classNameBody?: string
  showHeader?: boolean
  isLoading?: boolean
  loadingCount?: number
  rowClassName?: string
  inner?: boolean
  rowKey?: (rowData: T, idx?: number, data?: T[]) => string | null
  rowVars?: (data?: T) => V
  rowHref?: TableRowHref<T>
  rowProps?: TableRowProps | ((data?: T, idx?: number) => TableRowProps)
}
