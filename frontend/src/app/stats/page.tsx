import { Suspense } from 'react'

import { getWarehouseDashboard } from '@/actions/warehouse'
import Loader from '@/components/atoms/Loader'
import WarehouseDashboardAnalyzer from '@/components/feature/WarehouseDashboard/WarehouseDashboardAnalyzer'

import styles from './_assets/page.module.scss'

export default async function PageStats({
  searchParams,
}: {
  searchParams?: { [key: string]: string | undefined }
}) {
  const view = searchParams?.view ?? ''
  const dashboard = await getWarehouseDashboard('network-activities')

  if (!dashboard) {
    return null
  }

  return (
    <Suspense fallback={<Loader className={styles.burn} />}>
      <WarehouseDashboardAnalyzer dashboard={dashboard} view={view} params={searchParams} />
    </Suspense>
  )
}
