'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'

import { AnchorHTMLAttributes, FC, ReactNode } from 'react'

import clsx from 'clsx'
import { UrlObject, format } from 'url'

import { useDidMount } from '@/hooks/useDidMount'
import { useIsDesktop } from '@/hooks/useIsDesktop'

import styles from './MainMenu.module.scss'

export type AppNavigationMainMenuItemProps = Omit<
  AnchorHTMLAttributes<HTMLAnchorElement>,
  'href'
> & {
  isDisabled?: boolean
  icon?: ReactNode
  caption: string
  href: string | UrlObject
  isCollapsable?: boolean
}

export const AppNavigationMainMenuItem: FC<AppNavigationMainMenuItemProps> = ({
  icon,
  caption,
  href,
  className,
  isDisabled,
  isCollapsable,
  ...rest
}) => {
  const pathname = usePathname()
  const isMounted = useDidMount()
  const isDesktop = useIsDesktop()

  const commonProps = {
    className: clsx(
      styles.link,
      {
        [styles.active]:
          (href !== '/' && pathname.startsWith(format(href))) || pathname === format(href),
      },
      className
    ),
    'data-tooltip-content': caption,
    'data-tooltip-id': 'desktop-tooltip',
    ...rest,
  }

  const content = (
    <>
      <span className={styles.icon}>{icon}</span> <span className={styles.caption}>{caption}</span>
    </>
  )

  return (
    <li
      className={clsx(styles.item, {
        [styles.collapsed]: isMounted && isCollapsable && !isDesktop,
      })}>
      {isDisabled && (
        <span {...commonProps} data-tooltip-place="right">
          {content}
        </span>
      )}
      {!isDisabled && (
        <Link {...commonProps} href={href} data-tooltip-place="right">
          {content}
        </Link>
      )}
    </li>
  )
}
