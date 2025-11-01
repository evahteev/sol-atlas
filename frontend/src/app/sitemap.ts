import type { MetadataRoute } from 'next'

import { getWarehouseDashboards } from '@/services/warehouse-redash'

export const dynamic = 'force-dynamic'

const BASE_URL = process.env.APPLICATION_URL

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  // Fetch all dashboards tagged as 'content'
  const dashboards = await getWarehouseDashboards('content')

  // Map slugs to URLs
  const contentUrls = (dashboards ?? []).map((dashboard) => ({
    url: `${BASE_URL}/content/${dashboard.slug}`,
    lastModified: new Date(), // Optionally use dashboard.updatedAt if available
  }))

  // First-level URLs
  const firstLevelUrls = [
    { url: `${BASE_URL}/`, lastModified: new Date() },
    { url: `${BASE_URL}/about`, lastModified: new Date() },
    { url: `${BASE_URL}/admin`, lastModified: new Date() },
    // { url: `${BASE_URL}/aifeed`, lastModified: new Date() },
    { url: `${BASE_URL}/agents`, lastModified: new Date() },
    // { url: `${BASE_URL}/analytics`, lastModified: new Date() },
    // { url: `${BASE_URL}/buy`, lastModified: new Date() },
    // { url: `${BASE_URL}/chests`, lastModified: new Date() },
    { url: `${BASE_URL}/content`, lastModified: new Date() },
    { url: `${BASE_URL}/dashboards`, lastModified: new Date() },
    // { url: `${BASE_URL}/error`, lastModified: new Date() },
    // { url: `${BASE_URL}/flow`, lastModified: new Date() },
    // { url: `${BASE_URL}/launcher`, lastModified: new Date() },
    { url: `${BASE_URL}/leaderboards`, lastModified: new Date() },
    // { url: `${BASE_URL}/login`, lastModified: new Date() },
    // { url: `${BASE_URL}/process`, lastModified: new Date() },
    // { url: `${BASE_URL}/run`, lastModified: new Date() },
    // { url: `${BASE_URL}/send`, lastModified: new Date() },
    // { url: `${BASE_URL}/spend`, lastModified: new Date() },
    // { url: `${BASE_URL}/staking`, lastModified: new Date() },
    // { url: `${BASE_URL}/swap`, lastModified: new Date() },
    { url: `${BASE_URL}/tasks`, lastModified: new Date() },
    // { url: `${BASE_URL}/test`, lastModified: new Date() },
    // { url: `${BASE_URL}/token`, lastModified: new Date() },
    // { url: `${BASE_URL}/tokens`, lastModified: new Date() },
    // { url: `${BASE_URL}/topup`, lastModified: new Date() },
  ]

  return [...firstLevelUrls, ...contentUrls]
}
