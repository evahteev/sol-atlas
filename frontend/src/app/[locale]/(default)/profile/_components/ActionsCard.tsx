'use client'

import styles from '../_assets/page.module.scss'

interface Action {
  id: string
  title: string
  description: string
  icon: string
  category: string
  difficulty: 'Easy' | 'Medium' | 'Hard'
  reward: number
  estimatedTime: string
}

interface ActionsCardProps {
  actions: Action[]
}

export function ActionsCard({ actions }: ActionsCardProps) {
  const getDifficultyColor = (difficulty: string) => {
    switch (difficulty) {
      case 'Easy':
        return '#22D49F'
      case 'Medium':
        return '#FAA61A'
      case 'Hard':
        return '#F09000'
      default:
        return '#64748b'
    }
  }

  return (
    <div className={styles.profileStatsCard}>
      <div className={styles.actionsHeader}>
        <h3 className={styles.profileSubtitle}>Available Actions</h3>
        <span className={styles.actionsCount}>{actions.length} available</span>
      </div>

      <div className={styles.actionsList}>
        {actions.map((action) => (
          <div key={action.id} className={styles.actionItem}>
            <div className={styles.actionIcon}>
              <span className={styles.actionEmoji}>{action.icon}</span>
            </div>
            <div className={styles.actionInfo}>
              <div className={styles.actionHeader}>
                <h4 className={styles.actionTitle}>{action.title}</h4>
                <span
                  className={styles.actionDifficulty}
                  style={{
                    color: getDifficultyColor(action.difficulty),
                    backgroundColor: `${getDifficultyColor(action.difficulty)}20`,
                  }}>
                  {action.difficulty}
                </span>
              </div>
              <p className={styles.actionDescription}>{action.description}</p>
              <div className={styles.actionDetails}>
                <span className={styles.actionReward}>💰 {action.reward} CAPS</span>
                <span className={styles.actionTime}>⏱️ {action.estimatedTime}</span>
                <span className={styles.actionCategory}>{action.category}</span>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
