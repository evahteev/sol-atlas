import type { Metadata } from 'next'

import { getTranslations } from 'next-intl/server'
import { env } from 'next-runtime-env'

import auth from '@/auth'
import RequireLogin from '@/components/composed/RequireLogin'
import Tabs from '@/components/composed/Tabs'
import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
import { ApplicationSettings } from '@/framework/config'

import { PageQuestsList } from './_components/list/list'

import styles from './_assets/page.module.scss'

type SearchParams = Promise<Record<string, string>>

const { pointsToken, NATIVE_CURRENCY_SYMBOL } = (
  await import(`@/framework/${process.env.NEXT_PUBLIC_CI_PROJECT_NAME}/config`)
).ApplicationSettings as ApplicationSettings

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'Metadata' })
  const appName = env('NEXT_PUBLIC_APP_NAME') || 'Axioma 24'

  return {
    title: t('pages.tasks.title', { appName }),
    description: t('pages.tasks.description', { appName }),
    openGraph: {
      title: t('pages.tasks.title', { appName }),
      description: t('pages.tasks.description', { appName }),
      type: 'website',
      locale,
    },
    twitter: {
      card: 'summary_large_image',
      title: t('pages.tasks.title', { appName }),
      description: t('pages.tasks.description', { appName }),
    },
  }
}

export default async function PageQuests(props: { searchParams?: SearchParams }) {
  const t = await getTranslations('Tasks')
  const session = await auth()

  const tab = (await props.searchParams)?.tab
  const isDefaultTab = tab !== 'mainnet'
  const isForOnboarding = !!session?.user?.is_block

  const tabs = []

  if (!isForOnboarding) {
    tabs.push(
      ...[
        {
          caption: pointsToken.symbols?.[0] || 'POINTS',
          href: '?',
          isActive: isDefaultTab,
        },
        {
          caption: NATIVE_CURRENCY_SYMBOL || 'GURU',
          href: `?tab=mainnet`,
          isActive: tab === 'mainnet',
        },
      ]
    )
  }

  if (isForOnboarding) {
    tabs.push({
      caption: t('onboarding'),
      isActive: true,
    })
  }

  return (
    <RequireLogin>
      <div className={styles.container}>
        <div className={styles.header}>
          <Caption variant="header" size="lg" className={styles.title}>
            {t('title')}
          </Caption>
        </div>

        <div className={styles.body}>
          <Tabs className={styles.tabs} tabs={tabs} />

          <Show if={isForOnboarding}>
            <PageQuestsList tab="onboarding" className={styles.list} />
          </Show>

          <Show if={!isForOnboarding}>
            <PageQuestsList tab={tab} className={styles.list} />
          </Show>
        </div>

        <Show if={!isForOnboarding}>
          <div className={styles.footer}>
            <div className={styles.aside}>
              {/* <TasksChest
                caption={`Weekly ${NATIVE_CURRENCY_SYMBOL} Chest`}
                image={<Image src={imageChest} className={styles.icon} alt="" />}
                actions={
                  isDefaultTab ? [{ href: '?tab=mainnet', caption: 'Earn Rewards' }] : undefined
                }>
                Complete tasks, claim rewards, repeat tomorrow. Act fast before the pool runs out!
              </TasksChest> */}
            </div>
          </div>
        </Show>
      </div>
    </RequireLogin>
  )
}
