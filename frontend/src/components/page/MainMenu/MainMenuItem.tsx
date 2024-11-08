'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

import { FC, ReactNode } from 'react'

import clsx from 'clsx'
import { UrlObject, format } from 'url'

import styles from './MainManu.module.scss'

export type MainMenuItemProps = {
  isDisabled?: boolean
  icon?: ReactNode
  caption: ReactNode
  href: string | UrlObject
  className?: string
}

export const MainMenuItem: FC<MainMenuItemProps> = ({
  icon,
  caption,
  href,
  className,
  isDisabled,
}) => {
  const pathname = usePathname()

  const commonProps = {
    className: clsx(styles.link, { [styles.active]: pathname.startsWith(format(href)) }, className),
  }

  const content = (
    <>
      <span className={styles.icon}>{icon}</span> <span className={styles.caption}>{caption}</span>
    </>
  )

  if (isDisabled) {
    return <span {...commonProps}>{content}</span>
  }

  return (
    <Link {...commonProps} href={href}>
      {content}
    </Link>
  )
}
