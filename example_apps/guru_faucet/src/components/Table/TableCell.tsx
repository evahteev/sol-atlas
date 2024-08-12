import { FC, ReactNode, createElement } from 'react'

import clsx from 'clsx'

import styles from './Table.module.scss'

type TableCellProps = {
  children?: ReactNode | ReactNode[]
  className?: string
  isHeader?: boolean
  isLinkRow?: boolean
}

export const TableCell: FC<TableCellProps> = ({ children, className, isHeader, isLinkRow }) => {
  const element = isLinkRow ? 'div' : isHeader ? 'th' : 'td'

  return createElement(
    element,
    { className: clsx(styles.tcell, { [styles.th]: isHeader }, className) },
    children
  )
}
