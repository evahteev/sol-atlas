import { PageDashboardsByTag } from '@/components/page/PageDashboardsByTag/PageDashboardsByTag'

type Params = Promise<{ tag?: string }>
type SearchParams = Promise<Record<string, string | undefined>>

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

export default async function PageDashboards({
  params,
  searchParams,
}: {
  params: Params
  searchParams?: SearchParams
}) {
  const { tag } = await params
  const search = await searchParams

  return <PageDashboardsByTag urlPrefix={`/dashboards/${tag}`} tag={tag} params={search} />
}
