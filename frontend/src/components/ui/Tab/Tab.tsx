import { AnchorHTMLAttributes, ButtonHTMLAttributes } from 'react'

import clsx from 'clsx'

import { ActivatedLink, Caption } from '..'

import styles from './Tab.module.scss'

export type TabLinkProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
  href: string
  isActive?: boolean
  exact?: boolean
}

export type TabButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  href?: never
  isActive?: boolean
  exact?: never
}

export type TabProps = TabLinkProps | TabButtonProps

export function Tab({ isActive, children, href, className, exact = false }: TabProps) {
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
        <Caption variant="header" strong={true}>
          {children}
        </Caption>
      </ActivatedLink>
    )
  }

  return (
    <button className={tabClassName}>
      <Caption variant="header" strong={true}>
        {children}
      </Caption>
    </button>
  )
}
