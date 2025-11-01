import RequireLogin from '@/components/composed/RequireLogin'

import { LoginRedirectHandler } from './LoginRedirectHandler'

import styles from './_assets/page.module.scss'

export default async function PageLogin() {
  return (
    <>
      <RequireLogin className={styles.container} />
      <LoginRedirectHandler />
    </>
  )
}
