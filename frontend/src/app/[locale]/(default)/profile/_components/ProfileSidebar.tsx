import JazzIcon from '@/components/atoms/JazzIcon'
import IconEdit from '@/images/icons/edit.svg'
import IconExit from '@/images/icons/exit.svg'
import IconFlash from '@/images/icons/flash.svg'
import IconSettings from '@/images/icons/settings.svg'
import IconStars from '@/images/icons/stars.svg'
import IconStats from '@/images/icons/stats.svg'
import IconDiscord from '@/images/socials/discord.svg'
import IconTelegram from '@/images/socials/telegram.svg'
import IconX from '@/images/socials/x.svg'
import IconYouTube from '@/images/socials/youtube.svg'
import { Session } from '@/lib/session'

import { UserProfile } from '../_types/profile'

import styles from '../_assets/page.module.scss'

interface ProfileSidebarProps {
  user: UserProfile
  session: Session | null
}

export function ProfileSidebar({ user, session }: ProfileSidebarProps) {
  return (
    <div className={styles.sidebarContainer}>
      {/* Avatar Section */}
      <div className={styles.avatarSection}>
        <div className={styles.avatarWrapper}>
          <JazzIcon size={120} seed={1} />
        </div>
        <h2 className={styles.userName}>{user.name}</h2>
        <p className={styles.userTagline}>Building the future of decentralized communities.</p>
        <div className={styles.userBalance}>
          <span className={styles.balanceAmount}>{user.caps.toLocaleString()}</span>
          <span className={styles.balanceLabel}>GURU</span>
        </div>
      </div>

      {/* Social Icons */}
      <div className={styles.socialIcons}>
        <button className={styles.socialIcon} title="Telegram">
          <IconTelegram className={styles.socialIconSvg} />
        </button>
        <button className={styles.socialIcon} title="X (Twitter)">
          <IconX className={styles.socialIconSvg} />
        </button>
        <button className={styles.socialIcon} title="Discord">
          <IconDiscord className={styles.socialIconSvg} />
        </button>
        <button className={styles.socialIcon} title="YouTube">
          <IconYouTube className={styles.socialIconSvg} />
        </button>
      </div>

      {/* Community Info */}
      <div className={styles.communityInfo}>
        <p className={styles.communityText}>In community since: August 4, 2025</p>
        <div className={styles.levelRankInfo}>
          <div className={styles.levelInfo}>
            <IconStars className={styles.levelRankIcon} />
            <span>Level: {user.level}</span>
          </div>
          <div className={styles.rankInfo}>
            <IconFlash className={styles.levelRankIcon} />
            <span>Rank: #{user.rank}</span>
          </div>
        </div>
      </div>

      {/* Navigation Menu */}
      <nav className={styles.navigationMenu}>
        <button className={styles.navItem}>
          <IconStats className={styles.navIcon} />
          <span className={styles.navText}>My profile</span>
        </button>
        <button className={styles.navItem}>
          <IconSettings className={styles.navIcon} />
          <span className={styles.navText}>Tools</span>
        </button>
        <button className={styles.navItem}>
          <IconEdit className={styles.navIcon} />
          <span className={styles.navText}>Edit profile</span>
        </button>
        <button className={styles.navItem}>
          <IconTelegram className={styles.navIcon} />
          <span className={styles.navText}>Support</span>
        </button>
      </nav>

      {/* Logout Button */}
      {session && (
        <button className={styles.logoutButton}>
          <IconExit className={styles.logoutIcon} />
          Log out
        </button>
      )}
    </div>
  )
}
