import Caption from '@/components/ui/Caption'
import { getWarehouseQueryResponse } from '@/services/warehouse-redash'

import { PageLauncherDashboardStats } from './stats'
import { PageLauncherDashboardTable } from './table'

import styles from './dashboard.module.scss'

export const PageLauncherDashboard = async () => {
  const [stats, table] = await Promise.all([
    getWarehouseQueryResponse('guru_network_ecosystem_overview', {}, 5 * 60),
    getWarehouseQueryResponse('live_apps_leaderboard', {}, 5 * 60),
  ])

  return (
    <>
      <div className={styles.container}>
        <div className={styles.header}>
          <Caption variant="body" size="lg" className={styles.title}>
            GURU Network Ecosystem Overview
          </Caption>
        </div>
        <div className={styles.body}>
          <PageLauncherDashboardStats className={styles.stats} initialData={stats ?? undefined} />
        </div>
      </div>

      <div className={styles.container}>
        <div className={styles.header}>
          <Caption variant="body" size="lg" className={styles.title}>
            Live Apps Leaderboard
          </Caption>
          <span className={styles.description}>The communities shaping the next wave of Web3</span>
        </div>
        <div className={styles.body}>
          <PageLauncherDashboardTable initialData={table ?? undefined} />
        </div>
      </div>
    </>
  )
}
