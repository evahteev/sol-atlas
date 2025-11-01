import clsx from 'clsx'

import { Stat, StatProps } from './Stat'

import styles from './Stats.module.scss'

export type StatsProps = {
  className?: string
  items: StatProps[]
}

export function Stats({ items, className }: StatsProps) {
  return (
    <div className={clsx(styles.container, className)}>
      {items.map((item, idx) => {
        return <Stat {...item} className={clsx(styles.stat, item.className)} key={idx} />
      })}
    </div>
  )
}
