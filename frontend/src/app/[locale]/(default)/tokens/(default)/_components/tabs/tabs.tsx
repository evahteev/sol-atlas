'use client'

import { useSelectedLayoutSegment } from 'next/navigation'

import { FC } from 'react'

import { useTranslations } from 'next-intl'

import Tabs from '@/components/composed/Tabs'
import IconDiamond from '@/images/icons/diamond.svg'
import IconFire from '@/images/icons/fire.svg'
import IconRocket from '@/images/icons/fire.svg'
import IconFlash from '@/images/icons/flash.svg'
import IconSkull from '@/images/icons/skull.svg'

import styles from './tabs.module.scss'

export const TokensExplorerTabs: FC = () => {
  const t = useTranslations('Tokens.tabs')
  const view = useSelectedLayoutSegment()

  const isDefaultView = !['trending', 'top', 'gainers', 'losers', 'recent'].includes(view ?? '')

  return (
    <Tabs
      className={styles.tabs}
      tabs={[
        {
          caption: t('categories'),
          isActive: isDefaultView,
          href: '/tokens/',
        },
        {
          caption: t('topVolume'),
          isActive: view === 'top',
          href: '/tokens/top',
          icon: <IconDiamond className={styles.icon} />,
        },
        {
          caption: t('trending'),
          isActive: view === 'trending',
          href: '/tokens/trending',
          icon: <IconFire className={styles.icon} />,
        },
        {
          caption: t('degenMode'),
          isActive: view === 'recent',
          href: '/tokens/recent',
          icon: <IconFlash className={styles.icon} />,
        },
        {
          caption: t('gainers'),
          isActive: view === 'gainers',
          href: '/tokens/gainers',
          icon: <IconRocket className={styles.icon} />,
        },
        {
          caption: t('losers'),
          isActive: view === 'losers',
          href: '/tokens/losers',
          icon: <IconSkull className={styles.icon} />,
        },
      ]}
    />
  )
}
