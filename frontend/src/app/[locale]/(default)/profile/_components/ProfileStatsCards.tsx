'use client'

import { ProfileStats } from '../_types/profile'

import styles from '../_assets/page.module.scss'

interface ProfileStatsCardsProps {
  stats: ProfileStats
}

export function ProfileStatsCards({ stats }: ProfileStatsCardsProps) {
  return (
    <>
      {/* Card 1 (Left): Orders + Total Earned */}
      <div className={styles.profileStatsCard}>
        <div className={styles.profileStatItem}>
          <div className={styles.profileStatValue} style={{ color: '#22D49F' }}>
            {stats.totalActions.toLocaleString()}
          </div>
          <div className={styles.profileStatLabel}>Orders completed</div>
        </div>
        <div className={styles.profileStatItem}>
          <div className={styles.profileStatValue} style={{ color: '#FAA61A' }}>
            $8,012
          </div>
          <div className={styles.profileStatLabel}>Total earned</div>
        </div>
      </div>

      {/* Card 2 (Right): Average Score + Training Completion */}
      <div className={styles.profileStatsCard}>
        <div className={styles.profileStatItem}>
          <div className={styles.profileStatValue} style={{ color: '#9488F0' }}>
            {stats.averageRating}/5 ⭐
          </div>
          <div className={styles.profileStatLabel}>Average score</div>
        </div>
        <div className={styles.profileStatItem}>
          <div className={styles.profileStatValue} style={{ color: '#F09000' }}>
            98.4%
          </div>
          <div className={styles.profileStatLabel}>Completion of training</div>
        </div>
      </div>
    </>
  )
}
