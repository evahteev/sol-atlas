import { AnchorHTMLAttributes, ButtonHTMLAttributes } from 'react'

import clsx from 'clsx'
import { UrlObject } from 'url'

import ActivatedLink from '../ActivatedLink'
import Caption from '../Caption'

import styles from './Tab.module.scss'

export type TabLinkProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
  href: string | UrlObject
  isActive?: boolean
  exact?: boolean
}

export type TabButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  href?: never
  isActive?: boolean
  exact?: never
}

export type TabProps = TabLinkProps | TabButtonProps

export function Tab({ isActive, children, href, className, exact = false, ...props }: TabProps) {
  const tabClassName = clsx(styles.container, className, {
    [styles.active]: isActive,
  })

  if (href) {
    return (
      <ActivatedLink
        className={tabClassName}
        activeClassName={styles.active}
        href={href}
        exact={exact}>
        <Caption variant="body" size="lg">
          {children}
        </Caption>
      </ActivatedLink>
    )
  }

  return (
    <button className={tabClassName} {...(props as ButtonHTMLAttributes<HTMLButtonElement>)}>
      <Caption variant="body" size="lg">
        {children}
      </Caption>
    </button>
  )
}
