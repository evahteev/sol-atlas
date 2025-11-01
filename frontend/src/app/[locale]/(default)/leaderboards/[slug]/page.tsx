import { PageDashboardsByTag } from '@/components/page/PageDashboardsByTag/PageDashboardsByTag'

type Params = Promise<{ slug: string; tag: string }>
type SearchParams = Promise<Record<string, string | undefined>>

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

export default async function PageAnalyticsBySlug({
  params,
  searchParams,
}: {
  params: Params
  searchParams?: SearchParams
}) {
  const { slug } = await params
  const search = await searchParams

  return (
    <PageDashboardsByTag tag="leaderboards" slug={slug} params={search} urlPrefix="/leaderboards" />
  )
}
