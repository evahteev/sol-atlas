import Link from 'next/link'

import { createElement } from 'react'

import clsx from 'clsx'
import { format } from 'url'

import TooltipAnchor from '../TooltipAnchor'
import { TableColumnProps, TableRowHref, TableRowProps } from './Table'
import { TableCell } from './TableCell'

import styles from './Table.module.scss'

export const useBodyRows = <T, V>(options: {
  columns: TableColumnProps<T, V>[]
  data?: T[]
  classNameTCell?: string
  rowClassName?: string
  rowVars?: (data?: T) => V
  rowHref?: TableRowHref<T>
  rowKey?: (rowData: T, idx?: number, data?: T[]) => string | null
  isLoading?: boolean
  loadingCount?: number
  isLinkRows?: boolean
  rowProps?: TableRowProps | ((data?: T, idx?: number) => TableRowProps)
}) => {
  const {
    columns,
    data,
    classNameTCell,
    rowClassName,
    rowKey,
    isLoading,
    loadingCount,
    rowVars,
    rowHref,
    isLinkRows,
    rowProps,
  } = options

  // const { isBloombergAppPortal, applicationApi, isBbProd } = useContext(BloombergContext)

  const dataArr = isLoading ? Array.from(Array(loadingCount || data?.length || 10)) : data

  return dataArr?.map((dataItem, rowIdx) => {
    const vars = rowVars?.(dataItem)

    const cells = columns.map((column, cellIdx) => {
      const className = clsx(
        styles[column.type || 'text'],
        styles[column.modifier || 'default'],
        column.className
      )

      const cellDisplay = column.render
        ? column.render({
            data: dataItem || ({} as T),
            placeholder: column.placeholder,
            idx: rowIdx,
            vars,
          })
        : column.accessor
          ? dataItem?.[column.accessor] || column.placeholder
          : column.placeholder || <>&nbsp;</>

      return (
        <TableCell
          key={`${column.accessor}-${cellIdx}`}
          className={clsx(className, classNameTCell)}
          isLinkRow={isLinkRows}>
          <div className={styles.content}>{cellDisplay}</div>
        </TableCell>
      )
    })

    const href = typeof rowHref === 'function' ? format(rowHref?.(dataItem, rowIdx) || '') : rowHref

    const rowPropsData =
      (typeof rowProps === 'function' ? rowProps?.(dataItem, rowIdx) : rowProps) || {}

    const className = clsx(
      styles.trow,
      styles.tbodyrow,
      rowClassName,
      rowPropsData.className || undefined
    )

    const key = rowKey?.(dataItem, rowIdx, dataArr) || rowIdx

    if (isLinkRows && href) {
      // // in BloomberApp portal we aim to open new App Portal instances instead of new windows
      // if (isBloombergAppPortal && applicationApi) {
      //   return (
      //     <button
      //       key={key}
      //       {...rowPropsData}
      //       className={className}
      //       onClick={() => {
      //         const config = {
      //           width: 1366,
      //           height: 720,
      //           self_point: applicationApi.WindowPos.TOP_LEFT,
      //           other_point: applicationApi.WindowPos.TOP_RIGHT,
      //         }
      //         const args = {
      //           urlArg: href,
      //         }
      //         const progId = isBbProd ? BB_PROD_PROG_ID : BB_QA_PROG_ID
      //         applicationApi.createAppPortalComponent(progId, config, args)
      //       }}>
      //       {cells}
      //     </button>
      //   )
      // }

      return (
        <Link key={key} href={href} {...rowPropsData} className={className}>
          {cells}
        </Link>
      )
    }

    return createElement(isLinkRows ? 'div' : 'tr', { ...rowPropsData, key, className }, cells)
  })
}

export const useHeader = <T, V>({
  columns,
  rowClassName,
  isLinkRows,
}: {
  columns: TableColumnProps<T, V>[]
  rowClassName?: string
  isLinkRows?: boolean
}) => {
  const cells = columns.map((column, idx) => {
    const className = clsx(
      styles[column.type || 'text'],
      styles[column.modifier || 'default'],
      column.className
    )

    return (
      <TableCell
        isHeader
        key={`${column.accessor}-${idx}`}
        className={className}
        isLinkRow={isLinkRows}>
        {column.title || null} {!!column.tooltip && <TooltipAnchor text={column.tooltip} />}
      </TableCell>
    )
  })

  return createElement(
    isLinkRows ? 'div' : 'tr',
    { className: clsx(styles.trow, styles.theadrow, rowClassName) },
    cells
  )
}
