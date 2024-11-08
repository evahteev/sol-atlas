import { FC } from 'react'

import styles from './_assets/page.module.scss'

const PageBurn: FC = async () => {
  return (
    <div className={styles.container}>
      <iframe className={styles.body} src="https://app.paraswap.xyz" />
    </div>
  )
}

export default PageBurn
