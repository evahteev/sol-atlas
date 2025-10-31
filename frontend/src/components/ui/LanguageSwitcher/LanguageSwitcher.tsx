'use client'

import { FC } from 'react'

import clsx from 'clsx'
import { useLocale } from 'next-intl'

import Dropdown from '@/components/composed/Dropdown'
import { Link, usePathname } from '@/i18n/routing'
import IconGlobe from '@/images/icons/globe.svg'

import styles from './LanguageSwitcher.module.scss'

type LanguageSwitcherProps = {
  className?: string
}

export const LanguageSwitcher: FC<LanguageSwitcherProps> = ({ className }) => {
  const locale = useLocale()
  const pathname = usePathname()

  // Fallback to home if pathname is dynamic route
  const safeHref = pathname.includes('[') ? '/' : pathname

  return (
    <Dropdown
      caption={locale.toLocaleUpperCase()}
      icon={<IconGlobe className={styles.indicator} />}
      className={clsx(styles.container, className)}>
      <ul className={styles.list}>
        <li className={styles.item}>
          <Link
            href={safeHref as '/'}
            locale="en"
            className={clsx(styles.option, {
              [styles.active]: locale === 'en',
            })}>
            English
          </Link>
        </li>
        <li className={styles.item}>
          <Link
            href={safeHref as '/'}
            locale="ru"
            className={clsx(styles.option, {
              [styles.active]: locale === 'ru',
            })}>
            Русский
          </Link>
        </li>
      </ul>
    </Dropdown>
  )
}
