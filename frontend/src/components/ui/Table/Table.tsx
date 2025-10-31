import { createElement } from 'react'

import clsx from 'clsx'

import { useBodyRows, useHeader } from './hooks'
import { TableProps } from './types'

import styles from './Table.module.scss'

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
  classNameBody,
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
    classNameTCell,
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
      <div className={clsx(styles.body, classNameBody)}>
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
                  className: clsx(
                    styles.thead,
                    {
                      [styles.loading]: isLoading,
                    },
                    classNameTHead
                  ),
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
