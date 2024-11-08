import { FC, PropsWithChildren, ReactNode } from 'react'

import clsx from 'clsx'

import { Caption } from '@/components/ui'

import styles from './section.module.scss'

type ProfileWalletsSectionProps = PropsWithChildren & {
  className?: string
  title?: ReactNode
}
export const ProfileWalletsSection: FC<ProfileWalletsSectionProps> = ({
  className,
  title,
  children,
}) => {
  return (
    <section className={clsx(styles.container, className)}>
      <div className={styles.header}>
        <Caption variant="body" size="sm" className={styles.title}>
          {title}
        </Caption>
      </div>
      <div className={styles.body}>{children}</div>
    </section>
  )
}
