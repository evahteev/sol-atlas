import { FC, PropsWithChildren } from 'react'

import clsx from 'clsx'

import styles from './Prop.module.scss'

type ProfileProp = PropsWithChildren & {
  className?: string
  caption: string
}

export const ProfileProp: FC<ProfileProp> = ({ className, caption, children }) => {
  return (
    <div className={clsx(styles.container, className)}>
      <strong className={styles.header}>{caption}</strong>
      <div className={styles.body}>{children}</div>
    </div>
  )
}
