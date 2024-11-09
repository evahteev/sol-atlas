import clsx from 'clsx'

import styles from './GeneratedArt.module.scss'

export default function GeneratedArtPlaceholder() {
  return (
    <div className={styles.container}>
      <div className={styles.containerImg}>
        <div className={clsx(styles.img, styles.loading)} />
      </div>
      <div className={styles.containerDetails}>
        <div className={styles.details}>
          <span className={styles.label}>Original art title</span>
          <span className={styles.name}>Loading...</span>
        </div>
        <div className={styles.details}>
          <span className={styles.label}>Description</span>
          <span>Loading...</span>
        </div>
      </div>
    </div>
  )
}
