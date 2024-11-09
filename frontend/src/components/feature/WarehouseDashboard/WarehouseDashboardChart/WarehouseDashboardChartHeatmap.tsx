import { CSSProperties, FC } from 'react'

import clsx from 'clsx'

import { formatNumber } from '@/utils/numbers'

import styles from './WarehouseDashboardChartHeatmap.module.scss'

export type HeatmapChartEntry = Record<string, string | number>
export type HeatmapChartData = HeatmapChartEntry[]
export type HeatmapChartProps = {
  data?: HeatmapChartData
  className?: string
  keys: { x: string; y: string; val: string }
  tickXFormatter?: (value: string) => string
  tickYFormatter?: (value: string) => string
  tooltipFormat?: (props: { x: string; y: string; value: string | number }) => string
}

export const WarehouseDashboardChartHeatmap: FC<HeatmapChartProps> = ({
  data,
  keys,
  className,
  tooltipFormat,
  tickXFormatter,
  tickYFormatter,
}) => {
  if (!data) {
    return null
  }

  const xKeys = [...new Set(data.map((row) => row[keys.x]))]
  const xDefaultArr = Object.fromEntries(
    xKeys.map((row) => {
      return [tickXFormatter?.(row.toString()) ?? row.toString(), null]
    })
  )

  let min: number | undefined, max: number | undefined
  const tableRows: Record<string, Record<string, number | null>> = {}

  data.forEach((row) => {
    const keyX = tickXFormatter?.(row[keys.x]?.toString()) ?? row[keys.x]?.toString()
    const keyY = tickYFormatter?.(row[keys.y]?.toString()) ?? row[keys.y]?.toString()

    if (!tableRows[keyY]) {
      tableRows[keyY] = { ...xDefaultArr }
    }

    const numberValue = Number(row[keys.val])

    if (min === undefined) {
      min = numberValue
    } else {
      min = Math.min(min, Number(row[keys.val]))
    }

    if (max === undefined) {
      max = numberValue
    } else {
      max = Math.max(max, Number(row[keys.val]))
    }

    tableRows[keyY][keyX] = numberValue
  })

  const rangeMin = min || 0
  const rangeMax = max || 0
  const rangeCap = rangeMax - rangeMin

  const renderRows = () => {
    const tableRowsArr = Object.entries(tableRows)

    const content = tableRowsArr.map(([yVal, row]) => {
      return (
        <tr key={yVal} className={styles.row}>
          <th className={styles.header}>{yVal}</th>
          {Object.entries(row).map(([xVal, value]) => {
            if (value === null) {
              return <td className={styles.empty} key={`${yVal}-${xVal}`} />
            }

            const percent = !rangeCap ? 0 : (value - rangeMin) / rangeCap
            const displayValue = tooltipFormat?.({ x: xVal, y: yVal, value }) ?? formatNumber(value)

            return (
              <td
                className={styles.cell}
                key={`${yVal}-${xVal}`}
                data-tooltip-id="app-tooltip"
                data-tooltip-content={`${displayValue}`}
                style={{ '--ratio': percent } as CSSProperties}
              />
            )
          })}
        </tr>
      )
    })

    const footer = (
      <tr className={styles.row}>
        <th className={styles.header} />
        {Object.entries(tableRowsArr[0][1]).map(([xVal]) => {
          return (
            <td className={styles.header} key={`footer-${xVal}`}>
              {xVal}
            </td>
          )
        })}
      </tr>
    )

    return (
      <>
        {content}
        {footer}
      </>
    )
  }

  return (
    <div className={clsx(styles.container, className)}>
      <table className={styles.table}>
        <tbody>{renderRows()}</tbody>
      </table>
    </div>
  )
}
