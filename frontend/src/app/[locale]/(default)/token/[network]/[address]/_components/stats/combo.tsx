import { FC, ReactNode } from 'react'

import Show from '@/components/ui/Show'

import styles from './combo.module.scss'

export const TokenOverviewStatsCombo: FC<{ main: ReactNode; aside?: ReactNode }> = ({
  main,
  aside,
}) => {
  return (
    <div className={styles.container}>
      <div className={styles.body}>{main}</div>
      <Show if={aside}>
        <div className={styles.aside}>{aside}</div>
      </Show>
    </div>
  )
}
