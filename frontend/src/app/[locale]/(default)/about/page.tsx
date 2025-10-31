import StateMessage from '@/components/composed/StateMessage'
import WarehouseDashboard from '@/components/feature/WarehouseDashboard'
import { getWarehouseDashboard } from '@/services/warehouse-redash/dashboards'

type SearchParams = Promise<{ [key: string]: string | undefined }>

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

export default async function PageStats(props: { searchParams?: SearchParams }) {
  const searchParams = await props.searchParams

  const dashboard = await getWarehouseDashboard('about')

  if (!dashboard) {
    return <StateMessage type="danger" caption="No dashboard found" />
  }

  return (
    <>
      <WarehouseDashboard dashboard={dashboard} params={searchParams} />
    </>
  )
}
