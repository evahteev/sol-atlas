import { getTranslations } from 'next-intl/server'

import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
import { getWarehouseDashboards } from '@/services/warehouse-redash'

import { PageMainFeedEntry } from './entry'

import styles from './feed.module.scss'

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

export default async function PageMainFeed() {
  const t = await getTranslations('AIFeed.feed')
  const dashboards = await getWarehouseDashboards('aifeed')

  if (!dashboards?.length) {
    return null
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Caption variant="body" size="lg" className={styles.title}>
          {t('title')}
        </Caption>
      </div>
      <div className={styles.body}>
        <Show if={dashboards?.length}>
          <ul className={styles.list}>
            {dashboards?.map((dashboard) => (
              <li key={dashboard.slug} className={styles.item}>
                <PageMainFeedEntry
                  className={styles.entry}
                  slug={dashboard.slug}
                  date={dashboard.updated_at}
                  translations={{
                    aiAgent: t('aiAgent'),
                    timeAgo: t('timeAgo'),
                  }}
                />
              </li>
            ))}
          </ul>
        </Show>
      </div>
    </div>
  )
}
