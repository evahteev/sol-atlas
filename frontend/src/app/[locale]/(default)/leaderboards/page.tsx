import type { Metadata } from 'next'

import { getTranslations } from 'next-intl/server'
import { env } from 'next-runtime-env'

import { PageDashboardsByTag } from '@/components/page/PageDashboardsByTag/PageDashboardsByTag'

type SearchParams = Promise<Record<string, string | undefined>>

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'Metadata' })
  const appName = env('NEXT_PUBLIC_APP_NAME') || 'Axioma 24'

  return {
    title: t('pages.leaderboards.title', { appName }),
    description: t('pages.leaderboards.description', { appName }),
    openGraph: {
      title: t('pages.leaderboards.title', { appName }),
      description: t('pages.leaderboards.description', { appName }),
      type: 'website',
      locale,
    },
    twitter: {
      card: 'summary_large_image',
      title: t('pages.leaderboards.title', { appName }),
      description: t('pages.leaderboards.description', { appName }),
    },
  }
}

export default async function PageLeaderboards({ searchParams }: { searchParams?: SearchParams }) {
  const search = await searchParams

  return <PageDashboardsByTag tag="leaderboards" urlPrefix="/leaderboards" params={search} />
}
