import Link from 'next/link'

import { FC, SVGAttributes } from 'react'

import clsx from 'clsx'

import IconInstagram from '@/images/icons/instagram.svg'
import IconTelegram from '@/images/icons/telegram.svg'
import IconWeb from '@/images/icons/web.svg'
import IconX from '@/images/icons/x.svg'

import styles from './ProfileSocials.module.scss'

type ProfileSocial = 'x' | 'telegram' | 'instagram' | 'web'

const ProfileSocialsIcons: Record<ProfileSocial, FC<SVGAttributes<SVGElement>>> = {
  x: IconX,
  telegram: IconTelegram,
  instagram: IconInstagram,
  web: IconWeb,
}

type ProfileSocialsProps = {
  className?: string
  items: Record<ProfileSocial, string>
}

export const ProfileSocials: FC<ProfileSocialsProps> = ({ className, items }) => {
  const entries = Object.entries(items)

  if (!entries.length) {
    return null
  }

  return (
    <div className={clsx(styles.container, className)}>
      <ul className={styles.list}>
        {entries.map(([key, url]) => {
          const Icon = ProfileSocialsIcons[key as ProfileSocial]
          return (
            <li key={key} className={styles.item}>
              <Link href={url} className={styles.link}>
                <Icon className={styles.icon} />
              </Link>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
