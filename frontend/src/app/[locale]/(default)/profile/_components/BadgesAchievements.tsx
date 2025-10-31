import { Achievement, Badge } from '../_types/profile'

import styles from '../_assets/page.module.scss'

interface BadgesAchievementsProps {
  badges: Badge[]
  achievements: Achievement[]
}

export function BadgesAchievements({ badges, achievements }: BadgesAchievementsProps) {
  const getRarityColor = (rarity: string) => {
    switch (rarity) {
      case 'common':
        return '#22D49F'
      case 'rare':
        return '#9488F0'
      case 'epic':
        return '#FAA61A'
      case 'legendary':
        return '#F09000'
      default:
        return '#64748b'
    }
  }

  return (
    <div className={styles.profileCard}>
      <h3 className={styles.profileTitle}>Badges & Achievements</h3>

      {/* Badges - 4x1 horizontal grid with square icons */}
      <div className={styles.profileBadgesSection}>
        <h4 className={styles.profileSubtitle}>Badges</h4>
        <div className={styles.badgesHorizontalGrid}>
          {badges.map((badge) => (
            <div key={badge.id} className={styles.badgeSquareCard}>
              <div
                className={styles.badgeSquareIcon}
                style={{ backgroundColor: getRarityColor(badge.rarity) }}>
                <span className={styles.badgeEmoji}>{badge.icon}</span>
              </div>
              <div className={styles.badgeSquareInfo}>
                <h5 className={styles.badgeSquareTitle}>{badge.name}</h5>
                <span className={styles.badgeSquareRarity}>{badge.rarity.toUpperCase()}</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Achievements - 4x1 horizontal grid with square icons */}
      <div className={styles.profileAchievementsSection}>
        <h4 className={styles.profileSubtitle}>Achievements</h4>
        <div className={styles.achievementsHorizontalGrid}>
          {achievements.map((achievement) => (
            <div key={achievement.id} className={styles.achievementSquareCard}>
              <div className={styles.achievementSquareIcon}>
                <span className={styles.achievementEmoji}>{achievement.icon}</span>
              </div>
              <div className={styles.achievementSquareInfo}>
                <h5 className={styles.achievementSquareTitle}>{achievement.name}</h5>
                <p className={styles.achievementSquareDescription}>{achievement.description}</p>
                <span className={styles.achievementPointsBadge}>{achievement.points} points</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
