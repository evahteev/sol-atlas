import type { Metadata } from 'next'

import { getTranslations } from 'next-intl/server'
import { env } from 'next-runtime-env'

import AIChat from '@/components/feature/AIChat'

import styles from './_assets/page.module.scss'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'Metadata' })
  const appName = env('NEXT_PUBLIC_APP_NAME') || 'Axioma 24'

  return {
    title: t('pages.agents.title', { appName }),
    description: t('pages.agents.description', { appName }),
    openGraph: {
      title: t('pages.agents.title', { appName }),
      description: t('pages.agents.description', { appName }),
      type: 'website',
      locale,
    },
    twitter: {
      card: 'summary_large_image',
      title: t('pages.agents.title', { appName }),
      description: t('pages.agents.description', { appName }),
    },
  }
}

export default async function PageAgents() {
  return <AIChat className={styles.chat} integrationId="luka" />
}
