import type { Metadata } from 'next'

import { getTranslations } from 'next-intl/server'
import { env } from 'next-runtime-env'

import auth from '@/auth'
import Banner from '@/components/composed/Banner'
import IconAI from '@/images/icons/aichat.svg'
import IconFolder from '@/images/icons/folder.svg'
import IconGlobe from '@/images/icons/globe.svg'
import IconTGChat from '@/images/icons/telegram-chat.svg'
import IconTG from '@/images/icons/telegram.svg'
import IconX from '@/images/icons/x.svg'
import { FlowClientObject } from '@/services/flow'
import { getWarehouseQueryResponse } from '@/services/warehouse-redash'

import ImageSupport from './_assets/support.svg'
import { PageCommunityConfig } from './_components/config'
import { PageCommunityDashboard } from './_components/dashboard'
import PageMainFeed from './_components/feed'
import { PageAIFeedProfile } from './_components/profile'

import styles from './_assets/page.module.scss'

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

const APP_CONFIG_KEY = 'app_config'
const appName = env('NEXT_PUBLIC_APP_NAME') || 'Axioma 24'

const S3Logo = env('NEXT_PUBLIC_APP_LOGO')

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'Metadata' })

  return {
    title: t('pages.aifeed.title', { appName }),
    description: t('pages.aifeed.description'),
    openGraph: {
      title: t('pages.aifeed.title', { appName }),
      description: t('pages.aifeed.description'),
      type: 'website',
      locale,
    },
    twitter: {
      card: 'summary_large_image',
      title: t('pages.aifeed.title', { appName }),
      description: t('pages.aifeed.description'),
    },
  }
}

export default async function PageCommunity() {
  const session = await auth()
  const t = await getTranslations('AIFeed')
  const dashboardT = await getTranslations('AIFeed.dashboard')
  const profileT = await getTranslations('AIFeed.profile')
  const appConfig = await FlowClientObject.config.get({ key: APP_CONFIG_KEY })

  const {
    application_url,
    bot_name,
    support_url = undefined,
    social_telegram_chat = undefined,
    social_telegram = undefined,
    social_x = undefined,
  } = appConfig.value

  const stats = await getWarehouseQueryResponse('admin_panel_combined', {}, 30 * 60)

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <PageCommunityConfig
          className={styles.config}
          caption={t('title', { appName })}
          description={t('description', { appName })}
          imageURL={S3Logo}
          props={{
            link: {
              icon: <IconFolder className={styles.icon} />,
              caption: t('appLink', { appName }),
              value: application_url,
              type: 'url',
            },
            bot: {
              icon: <IconAI className={styles.icon} />,
              caption: t('botLink', { appName }),
              value: `https://t.me/${bot_name}`,
              type: 'url',
            },
            support: {
              icon: <IconGlobe className={styles.icon} />,
              caption: t('supportLink'),
              value: support_url || '/flow/app_support',
              type: 'url',
            },
            tg: {
              icon: <IconTGChat className={styles.icon} />,
              caption: t('telegramChat'),
              value: social_telegram_chat,
              type: 'url',
            },
            chat: {
              icon: <IconTG className={styles.icon} />,
              caption: t('telegramChannel', { appName }),
              value: social_telegram,
              type: 'url',
            },
            x: {
              icon: <IconX className={styles.icon} />,
              caption: t('twitter', { appName }),
              value: social_x,
              type: 'url',
            },
          }}
        />
      </div>

      <main className={styles.body}>
        <PageCommunityDashboard
          initialData={stats ?? undefined}
          className={styles.dashboard}
          translations={{
            totalUsers: dashboardT('totalUsers'),
            actions: dashboardT('actions'),
            actionsUnit: dashboardT('actionsUnit'),
            actionsPrevious: dashboardT('actionsPrevious'),
            dailyActiveUsers: dashboardT('dailyActiveUsers'),
            dau: dashboardT('dau'),
            caps: dashboardT('caps'),
            usersDynamics: dashboardT('usersDynamics'),
            actionsDynamics: dashboardT('actionsDynamics'),
            capsDynamics: dashboardT('capsDynamics'),
          }}
        />

        <PageMainFeed />
      </main>

      <aside className={styles.footer}>
        <PageAIFeedProfile
          session={session}
          className={styles.profile}
          walletAddress={undefined}
          translations={{
            title: profileT('title'),
            adminPanel: profileT('adminPanel'),
          }}
        />

        <Banner
          caption={t('support.title')}
          image={<ImageSupport />}
          actions={[
            {
              caption: t('support.buttonText'),
              href: '/flow/app_support',
              isOutline: true,
              variant: 'secondary',
            },
          ]}>
          {t('support.description1')}
          <hr />
          {t('support.description2')}
        </Banner>
      </aside>
    </div>
  )
}
