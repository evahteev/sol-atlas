import type { Metadata } from 'next'
import { headers } from 'next/headers'

import { PropsWithChildren } from 'react'

import { getTranslations } from 'next-intl/server'
import { env } from 'next-runtime-env'

import { fetchChainList } from '@/actions/tokens'
import ProfileBar from '@/components/composed/ProfileBar'
import AppNavigation from '@/components/page/AppNavigation'
import { AppNavigationMainMenuItemProps } from '@/components/page/AppNavigation/MainMenu/MainMenuItem'
import IconAgents from '@/images/icons/aichat.svg'
import IconAIFeed from '@/images/icons/aifeed.svg'
import IconDiamond from '@/images/icons/diamond.svg'
import IconFlash from '@/images/icons/flash.svg'
import IconRocket from '@/images/icons/rocket.svg'
import IconTasks from '@/images/icons/tasks.svg'

import { LayoutAIChat } from '../[locale]/_components/aichat/aichat'

import styles from '../[locale]/_assets/layout.module.scss'

// Since this is the root layout, all fetch requests in the app
// that don't set their own cache option will be cached.
export const fetchCache = 'default-cache'

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: `${env('NEXT_PUBLIC_APP_NAME')} App – AI-Powered Blockchain Automations and Rewards`,
    description: `Join the ${env('NEXT_PUBLIC_APP_NAME')} on Telegram: Experience AI-powered blockchain automations, create decentralized applications, and earn rewards by participating in the network!`,
    icons: [env('NEXT_PUBLIC_APP_LOGO') || '/favicon.svg'],
    metadataBase: new URL(`https://${(await headers()).get('host')}`),
  }
}

// Menu links moved to component to use translations

export default async function LayoutDefault({ children }: PropsWithChildren) {
  const chains = await fetchChainList().then((res) => res ?? [])
  const t = await getTranslations('Navigation')

  const menuLinks: AppNavigationMainMenuItemProps[] = [
    {
      icon: <IconAIFeed />,
      href: '/aifeed',
      caption: t('aiFeed'),
    },
    {
      icon: <IconTasks />,
      href: '/tasks',
      caption: t('actions'),
    },
    {
      icon: <IconAgents />,
      href: '/agents',
      caption: t('aiHub'),
    },
    {
      icon: <IconDiamond />,
      href: '/content',
      caption: t('about'),
      isCollapsable: true,
    },
    {
      icon: <IconFlash />,
      href: '/leaderboards',
      caption: t('leaderboard'),
      isCollapsable: true,
    },
    {
      icon: <IconRocket />,
      href: '/launcher',
      caption: 'Application Launcher',
      isCollapsable: true,
    },
  ]

  return (
    <>
      <ProfileBar className={styles.profile} chains={chains} />

      <div className={styles.body} id="page-body">
        <div className={styles.content} id="page-content">
          {children}
        </div>

        <LayoutAIChat className={styles.chat} />
      </div>

      <div className={styles.footer} id="page-nav">
        <AppNavigation items={menuLinks} logoAlt={t('logoAlt')} />
      </div>
    </>
  )
}
