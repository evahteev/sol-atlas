import { FC } from 'react'

import clsx from 'clsx'

import styles from './Loading.module.scss'

type LoadingProps = {
  className?: string
}

export const Loading: FC<LoadingProps> = ({ className }) => {
  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.bars}>
        <span className={styles.bar} />
        <span className={styles.bar} />
        <span className={styles.bar} />
        <span className={styles.bar} />
        <span className={styles.bar} />
      </div>
      <div className={styles.loaderTitle}>LOADING</div>
    </div>
  )
}
