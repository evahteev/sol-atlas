'use client'

import Link from 'next/link'
import { ReadonlyURLSearchParams } from 'next/navigation'

import { AnchorHTMLAttributes, FC, ReactNode } from 'react'

import clsx from 'clsx'
import { UrlObject } from 'url'

import Show from '../Show'
import { AppMenuWallet } from './AppMenuWallet'

import styles from './AppMenu.module.scss'

export type AppMenuItemInnerItems =
  | AppMenuItem[]
  | ((params: {
      pathname?: string
      params?: { [key: string]: string }
      searchParams?: ReadonlyURLSearchParams
    }) => Promise<AppMenuItem[] | null>)

export type AppMenuItemParams = {
  pathname?: string
  params?: { [key: string]: string | string[] }
  searchParams?: ReadonlyURLSearchParams
}

export type AppMenuItem = {
  icon?: ReactNode
  title: string
  description?: string
  keywords?: string
  key: string
  url?: string | UrlObject
  linkProps?: Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'>
  isHidden?: boolean
  isDelimiter?: boolean
  match?: (params: AppMenuItemParams) => boolean
  searchTopics?: ReactNode[]
  onClick?: () => void
  related?: AppMenuItemInnerItems
}

export type AppMenuSection = AppMenuItem & {
  actions?: AppMenuItemInnerItems
}

type AppMenuProps = {
  className?: string
  hasWallet?: boolean
  logo?: ReactNode
}

export const AppMenu: FC<AppMenuProps> = ({ className, hasWallet, logo }) => {
  return (
    <div className={clsx(styles.container, className)}>
      <Show if={logo}>
        <Link href="/" className={styles.logo}>
          {logo}
        </Link>
      </Show>

      {hasWallet && <AppMenuWallet />}
    </div>
  )
}
