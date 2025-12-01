import clsx from 'clsx'
import { getTranslations } from 'next-intl/server'

import Text from '@/components/atoms/Text'
import Caption from '@/components/ui/Caption'

import { PageLauncherCTA } from './_components/cta'
import { PageLauncherDashboard } from './_components/dashboard'

import styles from './_assets/page.module.scss'

export const revalidate = 300

export default async function PageLauncher() {
  const t = await getTranslations('Launcher')

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Caption variant="header" size="lg" className={styles.title}>
          {t('title')}
        </Caption>
      </div>

      <div className={styles.body}>
        <PageLauncherCTA
          className={styles.cta}
          caption={t('firstCta.caption')}
          action={{
            caption: t('firstCta.button'),
            variant: 'success',
            size: 'lg',
            href: '/run/token_app',
          }}>
          <Text>
            <p style={{ marginBottom: '1rem' }}>{t('firstCta.description1')}</p>
            <p
              style={{
                marginTop: '1rem',
                fontSize: '0.85rem',
                color: 'var(--color-text-secondary)',
              }}>
              ⏱️ {t('firstCta.deploymentTime')}
            </p>
          </Text>
        </PageLauncherCTA>

        <PageLauncherDashboard />

        <PageLauncherCTA
          className={clsx(styles.cta, styles.last)}
          caption={t('secondCta.caption')}
          action={{
            caption: t('secondCta.button'),
            variant: 'success',
            size: 'lg',
            href: '/run/token_app',
          }}>
          <Text>
            <p>{t('secondCta.description1')}</p>
            <p
              style={{
                marginTop: '1rem',
                fontSize: '0.9rem',
                color: 'var(--color-text-secondary)',
              }}>
              {t('secondCta.description2', { count: '36K+' })}
            </p>
          </Text>
        </PageLauncherCTA>
      </div>
    </div>
  )
}
