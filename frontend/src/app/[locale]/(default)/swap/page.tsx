import type { Metadata } from 'next'

import { getTranslations } from 'next-intl/server'
import { env } from 'next-runtime-env'

import Loader from '@/components/atoms/Loader'
import StateMessage from '@/components/composed/StateMessage'
import QuestRunner from '@/components/feature/QuestRunner'

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
    title: t('pages.swap.title', { appName }),
    description: t('pages.swap.description'),
    openGraph: {
      title: t('pages.swap.title', { appName }),
      description: t('pages.swap.description'),
      type: 'website',
      locale,
    },
    twitter: {
      card: 'summary_large_image',
      title: t('pages.swap.title', { appName }),
      description: t('pages.swap.description'),
    },
  }
}

export default async function PageSwap() {
  const t = await getTranslations('Swap')

  return (
    <div className={styles.container}>
      <QuestRunner
        processDefinitionKey="swap_tokens_from_external_wallet"
        className={styles.body}
        startVariables={{
          token_sell: { type: 'String', value: '0x833589fcd6edb6e08f4c7c32d4f71b54bda02913-base' }, // USDC
          token_buy: { type: 'String', value: '0x0f1cfd0bb452db90a3bfc0848349463010419ab2-base' }, // GURU
          chain_id: { type: 'String', value: '8453' },
          dst_chain_id: { type: 'String', value: '8453' },
        }}
        isStartable
        content={{
          loader: <Loader className={styles.loader}>{t('loading.warmingUp')}</Loader>,
          starter: <Loader className={styles.loader}>{t('loading.startingSwap')}</Loader>,
          waiting: <Loader className={styles.loader}>{t('loading.oneMoment')}</Loader>,
          empty: (
            <StateMessage
              type="danger"
              className={styles.message}
              caption={t('errors.notAvailable')}
            />
          ),
        }}
      />
    </div>
  )
}
