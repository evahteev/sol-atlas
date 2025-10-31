import { CSSProperties, FC } from 'react'

import clsx from 'clsx'
import uniqolor from 'uniqolor'

import { formatNumber } from '@/utils/numbers'

import styles from './distribution.module.scss'

type TokensExplorerTableDistributionProps = {
  data: { value?: number; name?: string; color?: string }[]
  className?: string
}

export const TokensExplorerTableDistribution: FC<TokensExplorerTableDistributionProps> = ({
  className,
  data = [{}, {}, {}, {}],
}) => {
  const total = data.reduce((acc, curr) => acc + (curr?.value ?? 0), 0)
  const dataSorted = data.sort((a, b) => (b?.value ?? 0) - (a?.value ?? 0))
  const dataSliced = dataSorted.slice(0, 4)

  if (dataSorted.length > 4) {
    dataSliced[3] = {
      name: 'Others',
      color: 'grey',
      value: dataSorted.slice(4).reduce((acc, curr) => acc + (curr?.value ?? 0), 0),
    }
  }

  return (
    <div className={clsx(styles.container, className)}>
      <table className={styles.body}>
        <tbody className={styles.list}>
          {dataSliced.map((el, idx) => {
            const color = el.color ?? uniqolor(`${el.name}${idx}`).color
            const percent = ((el.value ?? 0) * 100) / total

            return (
              <tr
                className={styles.item}
                key={idx}
                style={{ '--_color': color, '--_value': `${percent}%` } as CSSProperties}>
                <td className={clsx(styles.cell, styles.title)}>
                  <span className={styles.data}>{el.name ?? <>&nbsp;</>}</span>
                </td>

                <td className={styles.cell}>
                  <span className={styles.bar} />
                </td>

                <td className={clsx(styles.cell, styles.value)}>
                  <span className={styles.data}>
                    {formatNumber(percent, { maximumFractionDigits: percent < 1 ? 4 : 2 })}%
                  </span>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
