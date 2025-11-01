import type { Metadata } from 'next'

import { FC } from 'react'

import { getTranslations } from 'next-intl/server'
import { env } from 'next-runtime-env'

import { fetchTokenTags } from '@/actions/tokens'

import { TokensTagsCloud } from './_components/cloud/cloud'

import styles from './_assets/page.module.scss'

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'Metadata' })
  const appName = env('NEXT_PUBLIC_APP_NAME') || 'GuruNetwork'

  return {
    title: t('pages.tokens.title', { appName }),
    description: t('pages.tokens.description'),
    openGraph: {
      title: t('pages.tokens.title', { appName }),
      description: t('pages.tokens.description'),
      type: 'website',
      locale,
    },
    twitter: {
      card: 'summary_large_image',
      title: t('pages.tokens.title', { appName }),
      description: t('pages.tokens.description'),
    },
  }
}

export const dynamic = 'force-dynamic'

const PageTokensExplorer: FC = async () => {
  const tagsList = (await fetchTokenTags()) ?? undefined

  return <TokensTagsCloud className={styles.cloud} tags={tagsList} />
}

export default PageTokensExplorer
