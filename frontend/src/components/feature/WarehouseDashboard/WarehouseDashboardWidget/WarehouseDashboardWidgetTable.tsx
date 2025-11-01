import { FC } from 'react'

import { marked } from 'marked'

import Table from '@/components/ui/Table'
import { TableColumnProps } from '@/components/ui/Table/types'
import TooltipAnchor from '@/components/ui/TooltipAnchor'
import {
  TWarehouseQueryResultData,
  TWarehouseVisualizationOptions,
} from '@/services/warehouse-redash/types'
import { formatAutoDetect } from '@/utils/format'
import { formatNumber } from '@/utils/numbers'

import styles from './WarehouseDashboardWidget.module.scss'

type WarehouseDashboardWidgetTableProps = {
  data?: TWarehouseQueryResultData
  className?: string
  isLoading?: boolean
  options?: TWarehouseVisualizationOptions
}

export const WarehouseDashboardWidgetTable: FC<WarehouseDashboardWidgetTableProps> = ({
  data,
  options,
  isLoading,
}) => {
  const columnsSource =
    options?.columns
      ?.filter((col) => col.visible)
      .sort((a, b) => (a.order || 0) - (b.order || 0)) ??
    data?.columns ??
    Array(4).fill({ type: '', name: '' })
  const columns =
    columnsSource?.map((col): TableColumnProps<Record<string, string | number>> => {
      const isNumber = ['float', 'integer', 'number'].includes(col.displayAs || col.type)

      const title = col.title || col.friendly_name || col.name

      return {
        accessor: col.name,
        title: (
          <>
            {title} <TooltipAnchor text={col.description} />
          </>
        ),
        type: ['float', 'integer', 'number'].includes(col.type) ? 'number' : 'text',
        render: ({ data }) => {
          if (isLoading) {
            return <div>&nbsp;</div>
          }

          const decimalsCount = col.numberFormat?.match(/\.(0+)/)?.[1]?.length
          const isPercent = col.numberFormat?.includes('%')
          const cellData = data[col.name]

          if (isNumber) {
            return (
              <div className={styles.tcellData}>
                {formatNumber(Number(cellData), {
                  maximumFractionDigits: decimalsCount || undefined,
                  suffix: isPercent ? '%' : undefined,
                })}
              </div>
            )
          }

          const parsedCellMarkup = marked.parse(formatAutoDetect(`${cellData ?? ''}`), {
            async: false,
          })

          return (
            <div
              className={styles.tcellData}
              dangerouslySetInnerHTML={{ __html: parsedCellMarkup }}
            />
          )
        },
      }
    }) ?? []

  const tableData = isLoading ? Array(5) : (data?.rows ?? [])

  return (
    <Table
      columns={columns}
      data={tableData}
      className={styles.table}
      classNameBody={styles.tableBody}
      isLoading={isLoading}
    />
  )
}
