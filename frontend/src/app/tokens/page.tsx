import { FC } from 'react'

import styles from './_assets/page.module.scss'

const PageBurn: FC = async () => {
  return (
    <div className={styles.container}>
      <iframe className={styles.body} src="https://v2.dex.guru/tokens" />
    </div>
  )
}

export default PageBurn
