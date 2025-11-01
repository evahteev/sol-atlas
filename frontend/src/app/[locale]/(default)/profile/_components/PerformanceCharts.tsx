import { CapsHistory, RankHistory } from '../_types/profile'

import styles from '../_assets/page.module.scss'

interface PerformanceChartsProps {
  rankHistory: RankHistory[]
  capsHistory: CapsHistory[]
}

export function PerformanceCharts({ rankHistory, capsHistory }: PerformanceChartsProps) {
  return (
    <>
      {/* Rank Dynamics Chart */}
      <div className={styles.profileCard}>
        <h4 className={styles.profileSubtitle}>Rank Dynamics</h4>
        <div className={styles.profileChart}>
          {rankHistory.map((entry, _index) => (
            <div key={entry.date} className={styles.profileChartBar}>
              <div
                className={styles.profileChartBarFill}
                style={{
                  height: `${Math.max(1, (entry.rank / 150) * 100)}%`,
                  backgroundColor: '#22D49F',
                }}
              />
              <span className={styles.profileChartLabel}>
                {new Date(entry.date).toLocaleDateString('en-US', { month: 'short' })}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* CAPs Dynamics Chart */}
      <div className={styles.profileCard}>
        <h4 className={styles.profileSubtitle}>CAPs Dynamics</h4>
        <div className={styles.profileChart}>
          {capsHistory.map((entry, _index) => (
            <div key={entry.date} className={styles.profileChartBar}>
              <div
                className={styles.profileChartBarFill}
                style={{
                  height: `${Math.max(1, (entry.caps / 1250) * 100)}%`,
                  backgroundColor: '#FAA61A',
                }}
              />
              <span className={styles.profileChartLabel}>
                {new Date(entry.date).toLocaleDateString('en-US', { month: 'short' })}
              </span>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
