'use client'

import dynamic from 'next/dynamic'
import Image from 'next/image'
import Link from 'next/link'

import { FC } from 'react'

import clsx from 'clsx'
import { useTranslations } from 'next-intl'
import { env } from 'next-runtime-env'

import { AppNavigationMainMenu } from './MainMenu/MainMenu'
import { AppNavigationMainMenuItemProps } from './MainMenu/MainMenuItem'

import styles from './AppNavigation.module.scss'

type AppNavigationProps = {
  items?: AppNavigationMainMenuItemProps[]
  logoAlt?: string
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
const ImageLogoFull = dynamic<any>(() => import(`skins/theme/assets/images/brand/logo-full.svg`))

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const ImageLogoSmall = dynamic<any>(() => import(`skins/theme/assets/images/brand/logo-small.svg`))

const S3Logo = env('NEXT_PUBLIC_APP_LOGO')

export const AppNavigation: FC<AppNavigationProps> = ({ items, logoAlt }) => {
  const t = useTranslations('Navigation')
  const effectiveLogoAlt = logoAlt || t('logoAlt')

  return (
    <>
      <Link href="/" className={styles.link}>
        {S3Logo && S3Logo !== 'None' && (
          <Image
            className={clsx(styles.logo, styles.small)}
            width="40"
            height="40"
            src={S3Logo}
            alt={effectiveLogoAlt}
          />
        )}
        {(!S3Logo || S3Logo === 'None') && (
          <>
            <ImageLogoFull className={clsx(styles.logo, styles.full)} />
            <ImageLogoSmall className={clsx(styles.logo, styles.small)} />
          </>
        )}
      </Link>

      <AppNavigationMainMenu items={items} className={styles.main} />
    </>
  )
}
