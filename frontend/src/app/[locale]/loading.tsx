import Loader from '@/components/atoms/Loader'

import styles from './_assets/layout.module.scss'

export default function RootLayoutLoader() {
  return <Loader className={styles.loader} />
}
