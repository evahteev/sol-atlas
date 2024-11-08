import { FC, PropsWithChildren } from 'react'

import { Tab } from '@/components/ui'

import styles from './_assets/layout.module.scss'

const PageActionsLayout: FC = async ({ children }: PropsWithChildren) => {
  return (
    <>
      <div className={styles.tabs}>
        <Tab href="/actions/swap" exact={true}>
          Swap
        </Tab>
      </div>

      {children}
    </>
  )
}

export default PageActionsLayout
