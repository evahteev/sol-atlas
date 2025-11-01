import { ProfileStats } from '../_types/profile'

import styles from '../_assets/page.module.scss'

interface ProfileStatsGridProps {
  stats: ProfileStats
}

export function ProfileStatsGrid({ stats }: ProfileStatsGridProps) {
  return (
    <>
      {/* First card: Orders Completed + Average Score */}
      <div className={styles.profileCard}>
        <div className={styles.profileTextCenter}>
          <div className={styles.profileTitle} style={{ fontSize: '48px', color: '#22D49F' }}>
            {stats.totalActions}
          </div>
          <p className={styles.profileSubtitle}>Orders Completed</p>
        </div>
        <div className={styles.profileTextCenter} style={{ marginTop: '16px' }}>
          <div className={styles.profileTitle} style={{ fontSize: '32px', color: '#FAA61A' }}>
            {stats.averageRating}
          </div>
          <p className={styles.profileSubtitle}>Average Score</p>
        </div>
      </div>

      {/* Second card: Total Earned + Completion % */}
      <div className={styles.profileCard}>
        <div className={styles.profileTextCenter}>
          <div className={styles.profileTitle} style={{ fontSize: '48px', color: '#9488F0' }}>
            {stats.successfulTasks}
          </div>
          <p className={styles.profileSubtitle}>Total Earned</p>
        </div>
        <div className={styles.profileTextCenter} style={{ marginTop: '16px' }}>
          <div className={styles.profileTitle} style={{ fontSize: '32px', color: '#F09000' }}>
            {Math.round((stats.successfulTasks / stats.totalActions) * 100)}%
          </div>
          <p className={styles.profileSubtitle}>Training Completion</p>
        </div>
      </div>
    </>
  )
}
