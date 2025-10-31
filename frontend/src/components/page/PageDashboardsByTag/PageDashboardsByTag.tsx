import { redirect } from 'next/navigation'

import { FC, Suspense } from 'react'

import Loader from '@/components/atoms/Loader'
import StateMessage from '@/components/composed/StateMessage'
import { AIChatPrompt } from '@/components/feature/AIChat/AIChat'
import WarehouseDashboard from '@/components/feature/WarehouseDashboard'
import WarehouseDashboardAIChat from '@/components/feature/WarehouseDashboard/WarehouseDashboardAIChat'
import WarehouseDashboards from '@/components/feature/WarehouseDashboard/WarehouseDashboards'
import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
import { getWarehouseDashboard, getWarehouseDashboards } from '@/services/warehouse-redash'

import styles from './PageDashboardsByTag.module.scss'

type PageDashboardsByTag = {
  tag?: string
  slug?: string
  urlPrefix?: string
  prompts?: AIChatPrompt[]
  params?: Record<string, string | undefined>
}

const dashboardPrompts: Record<string, { label: string; value: string }[]> = {
  ['dex_guru_tokens']: [
    {
      label: 'Generate a concise and engaging Twitter post',
      value: `Generate a concise and engaging Twitter post summarizing key insights from the dashboard, including notable trends, market movements, and potential opportunities. Ensure it is data-driven and formatted for high engagement (e.g., emojis, hashtags, and a call to action). MUST USE dashboard_slug=dex_guru_tokens`,
    },
    {
      label: 'Give me a summary of this data',
      value: `Analyze the data in the dashboard and provide a summary of the most significant trends and anomalies, including explanations backed by data. MUST USE dashboard_slug=dex_guru_tokens`,
    },
    {
      label: 'Identify bullish or bearish trends',
      value: `Using dashboard, analyze user transaction behavior and price action to infer potential sentiment shifts, identifying any patterns that indicate bullish or bearish trends. MUST USE dashboard_slug=dex_guru_tokens`,
    },
  ],
}

export const PageDashboardsByTag: FC<PageDashboardsByTag> = async ({
  tag,
  slug,
  urlPrefix,
  prompts,
  params,
}) => {
  if (!tag) {
    return (
      <StateMessage type="danger" className={styles.error} caption="No dashboards tag specified" />
    )
  }

  const dashboards = await getWarehouseDashboards(tag)

  if (!dashboards?.length) {
    return (
      <StateMessage type="danger" className={styles.error} caption="No active dashboards found" />
    )
  }

  const dashboard = await getWarehouseDashboard(slug || dashboards[0].slug)

  if (dashboards?.length === 1 && dashboard) {
    return (
      <>
        <WarehouseDashboardAIChat
          prompts={prompts ?? dashboardPrompts[dashboard.slug]}
          entry={{ type: 'dashboard', id: dashboard.slug }}
        />
        <WarehouseDashboard dashboard={dashboard} params={params} />
      </>
    )
  }

  if (!slug) {
    redirect(`${urlPrefix}/${dashboards[0].slug}`)
  }

  return (
    <WarehouseDashboards prefix={urlPrefix} tag={tag} dashboards={dashboards} slug={slug}>
      <Show if={!slug}>
        <StateMessage className={styles.empty} caption="Please, select dashboard" />
      </Show>

      <Show if={!dashboard}>
        <StateMessage type="danger" className={styles.error} caption="No dashboard found" />
      </Show>

      {!!dashboard && (
        <>
          <Caption variant="header" size="lg" className={styles.title}>
            {dashboard.name}
          </Caption>

          <WarehouseDashboardAIChat
            prompts={prompts ?? dashboardPrompts[dashboard.slug]}
            entry={{ type: 'dashboard', id: dashboard.slug }}
          />
          <Suspense fallback={<Loader className={styles.loader}>Loading dashboard...</Loader>}>
            <WarehouseDashboard dashboard={dashboard} showTitle={false} params={params} />
          </Suspense>
        </>
      )}
    </WarehouseDashboards>
  )
}
