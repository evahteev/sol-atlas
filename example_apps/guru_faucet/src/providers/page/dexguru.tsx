import { ReactNode } from 'react'

import clsx from 'clsx'

import AppMenu from '@/components/AppMenu'
import Logo from '@/images/logo.svg'

import styles from './layout.module.scss'

export default function DexguruPageProvider({ children }: { children: ReactNode }) {
  return (
    <div className={styles.container}>
      <AppMenu
        className={clsx(styles.menu, styles.dexguru)}
        hasWallet={true}
        logo={<Logo className={styles.logo} />}
      />
      <main className={styles.body}>{children}</main>
    </div>
  )
}
