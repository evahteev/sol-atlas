import { FC } from 'react'

import {
  TWarehouseQueryResultData,
  TWarehouseVisualizationOptions,
} from '@/actions/warehouse/types'
import Table from '@/components/ui/Table'
import { TableColumnProps } from '@/components/ui/Table/Table'
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
      const isNumber = ['float', 'integer', 'number'].includes(col.type)

      const title =
        'title' in col ? col.title : 'friendly_name' in col ? col.friendly_name : col.name

      return {
        accessor: col.name,
        title,
        type: ['float', 'integer', 'number'].includes(col.type) ? 'number' : 'text',
        render: ({ data }) =>
          isLoading ? (
            <div>&nbsp;</div>
          ) : (
            <div className={styles.tcellData}>
              {isNumber && formatNumber(+data[col.name])}
              {!isNumber && `${data[col.name]}`}
            </div>
          ),
      }
    }) ?? []

  const tableData = isLoading ? Array(data?.rows?.length || 10) : (data?.rows ?? [])

  return <Table columns={columns} data={tableData} className={styles.table} isLoading={isLoading} />
}
