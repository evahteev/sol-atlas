import JazzIcon from '@/components/atoms/JazzIcon'

import { UserProfile } from '../_types/profile'

import styles from '../_assets/page.module.scss'

interface ProfileHeaderProps {
  user: UserProfile
}

export function ProfileHeader({ user }: ProfileHeaderProps) {
  return (
    <div className={styles.profileHeaderCard}>
      {/* Avatar */}
      <div className={styles.profileAvatar}>
        <JazzIcon size={96} seed={1} />
      </div>

      {/* User Info */}
      <div className={styles.profileUserInfo}>
        <h2 className={styles.profileTitle}>{user.name}</h2>
        <p className={styles.profileText}>Blockchain Developer & Community Contributor</p>

        {/* Stats below name */}
        <div className={styles.profileStats}>
          <span className={styles.profileCaption}>
            Joined {new Date(user.joinDate).toLocaleDateString()}
          </span>
          <span className={styles.profileCaption}>Level {user.level}</span>
          <span className={styles.profileCaption}>Rank #{user.rank}</span>
        </div>
      </div>

      {/* Right side - Badge and Balance */}
      <div className={styles.profileRightSide}>
        {/* Badge */}
        <div className={styles.profileBadge}>Mentor</div>

        {/* Balance */}
        <div className={styles.profileBalance}>
          <span>💰</span>
          <span>{user.caps} CAPS</span>
        </div>
      </div>
    </div>
  )
}
