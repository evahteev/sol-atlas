import { ReactNode, createElement } from 'react'

import clsx from 'clsx'
import { UrlObject } from 'url'

import { useBodyRows, useHeader } from './hooks'

import styles from './Table.module.scss'

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

export function Table<T, V>({
  title,
  columns,
  data,
  showHeader = true,
  className,
  classNameTable,
  classNameTHead,
  classNameTBody,
  classNameTCell,
  isLoading,
  loadingCount,
  rowClassName,
  inner,
  rowKey,
  rowVars,
  rowHref,
  rowProps,
}: TableProps<T, V>) {
  const isLinkRows = typeof rowHref !== 'undefined'

  const header = useHeader<T, V>({
    columns,
    rowClassName,
    isLinkRows,
  })

  const rows = useBodyRows<T, V>({
    columns,
    data,
    rowClassName,
    classNameTCell,
    isLoading,
    loadingCount,
    rowKey,
    rowVars,
    rowHref,
    rowProps,
    isLinkRows,
  })

  return (
    <div className={clsx(styles.container, { [styles.inner]: inner }, className)}>
      {!!title && <div className={styles.header}>{title}</div>}
      <div className={styles.body}>
        {createElement(
          isLinkRows ? 'div' : 'table',
          {
            className: clsx(styles.table, { [styles.loading]: isLoading }, classNameTable),
          },
          <>
            {showHeader &&
              createElement(
                isLinkRows ? 'div' : 'thead',
                {
                  className: clsx(styles.thead, {
                    [styles.loading]: isLoading,
                    classNameTHead,
                  }),
                },
                header
              )}

            {createElement(
              isLinkRows ? 'div' : 'tbody',
              {
                className: clsx(styles.tbody, { [styles.loading]: isLoading }, classNameTBody),
              },
              rows
            )}
          </>
        )}
      </div>
    </div>
  )
}
