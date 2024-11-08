import { FC, PropsWithChildren } from 'react'

import clsx from 'clsx'

import Loader from '@/components/atoms/Loader'
import { Caption } from '@/components/ui'

import styles from './Intro.module.scss'

type IntroProps = PropsWithChildren<{
  className?: string
  isLoading?: boolean
}>

export const Intro: FC<IntroProps> = ({ className, children, isLoading }) => {
  return (
    <div className={clsx(styles.container, { [styles.loading]: isLoading }, className)}>
      <div className={styles.header}>
        <Caption variant="header" size="xxl">
          Welcome!
        </Caption>
      </div>

      <div className={styles.body}>{children}</div>
      <div className={styles.footer}>
        <Loader className={styles.loader} />
      </div>
    </div>
  )
}
