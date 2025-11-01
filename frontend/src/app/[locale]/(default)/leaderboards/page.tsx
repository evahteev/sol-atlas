import { PageDashboardsByTag } from '@/components/page/PageDashboardsByTag/PageDashboardsByTag'

type SearchParams = Promise<Record<string, string | undefined>>

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

export default async function PageLeaderboards({ searchParams }: { searchParams?: SearchParams }) {
  const search = await searchParams

  return <PageDashboardsByTag tag="leaderboards" urlPrefix="/leaderboards" params={search} />
}
