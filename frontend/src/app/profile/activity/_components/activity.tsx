import Image from 'next/image'
import Link from 'next/link'

import { FC, PropsWithChildren } from 'react'

import { UTCDate } from '@date-fns/utc'
import clsx from 'clsx'

import { Show } from '@/components/ui'
import { getShortDate } from '@/utils/dates'
import { getShortAddress } from '@/utils/strings'

import styles from './activity.module.scss'

type ProfileActivityItemProps = PropsWithChildren & {
  className?: string
  date: UTCDate | string
  tx?: string
  image?: string
}

export const ProfileActivityItem: FC<ProfileActivityItemProps> = ({
  className,
  date,
  tx,
  image,
  children,
}) => {
  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.header}>
        <span className={styles.date}>{getShortDate(date)}</span>{' '}
        <Show if={tx}>
          <Link className={styles.tx} href={'/'}>
            {getShortAddress(tx)}
          </Link>
        </Show>
      </div>
      <div className={styles.body}>
        <Show if={image}>
          <div className={styles.illustration}>
            <Image src={image ?? ''} alt="" width={48} height={48} className={styles.icon} />
          </div>
        </Show>
        <div className={styles.content}>{children}</div>
      </div>
    </div>
  )
}
