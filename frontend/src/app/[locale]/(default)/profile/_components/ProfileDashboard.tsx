'use client'

import Dashboard from '@/components/composed/Dashboard'
import { getDate } from '@/utils/dates'

import { UserProfile } from '../_types/profile'

import styles from '../_assets/page.module.scss'

interface ProfileDashboardProps {
  user: UserProfile
}

export function ProfileDashboard({ user }: ProfileDashboardProps) {
  return (
    <Dashboard
      className={styles.dashboard}
      widgets={[
        // 4 Counters (3 columns each = 12 total)
        {
          type: 'counter',
          className: styles.counter,
          caption: 'Orders Completed',
          value: user.stats.totalActions,
        },
        {
          type: 'counter',
          className: styles.counter,
          caption: 'Average Score',
          value: user.stats.averageRating,
        },
        {
          type: 'counter',
          className: styles.counter,
          caption: 'Total Earned',
          value: user.stats.successfulTasks,
        },
        {
          type: 'counter',
          className: styles.counter,
          caption: 'Training Completion',
          value: Math.round((user.stats.successfulTasks / user.stats.totalActions) * 100),
          suffix: '%',
        },
        // 3 Charts (4 columns each = 12 total)
        {
          type: 'chart',
          caption: 'Rank Dynamics',
          className: styles.chart,
          data: user.rankHistory.map((item) => ({
            x: getDate(item.date),
            y: item.rank,
          })),
          color: '#22D49F',
        },
        {
          type: 'chart',
          caption: 'CAPs Dynamics',
          className: styles.chart,
          data: user.capsHistory.map((item) => ({
            x: getDate(item.date),
            y: item.caps,
          })),
          color: '#FAA61A',
        },
        {
          type: 'chart',
          caption: 'Performance Trend',
          className: styles.chart,
          data: user.rankHistory.map((item, index) => ({
            x: getDate(item.date),
            y: 100 - index * 10, // Mock performance trend
          })),
          color: '#9488F0',
        },
      ]}
    />
  )
}
