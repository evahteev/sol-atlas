import clsx from 'clsx'

import styles from './Rank.module.scss'

export function Rank({ rank }: { rank: number }) {
  const rankClassName = clsx(styles.container, { [styles.medal]: rank < 4 })
  const ranks: { [key: number]: string } = {
    1: '🥇',
    2: '🥈',
    3: '🥉',
  }
  return <div className={rankClassName}>{rank > 3 ? rank : ranks[rank]}</div>
}
