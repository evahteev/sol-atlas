import { getSessionWithUser } from '@/lib/dal'

import { ActionsCard } from './_components/ActionsCard'
import { BadgesAchievements } from './_components/BadgesAchievements'
import { CertificatesSection } from './_components/CertificatesSection'
import { MessagesCard } from './_components/MessagesCard'
import { PostsCard } from './_components/PostsCard'
import { ProfileSidebar } from './_components/ProfileSidebar'
import { ServicesCard } from './_components/ServicesCard'
import { HARDCODED_PROFILE_DATA } from './_types/profile'

import styles from './_assets/page.module.scss'

export default async function ProfilePage() {
  const session = await getSessionWithUser()

  // Use hardcoded data for development
  const profileData = HARDCODED_PROFILE_DATA

  return (
    <div className={styles.container}>
      {/* Header Section - Empty after removing charts */}
      <header className={styles.header}></header>

      {/* Main Content - Individual card layout */}
      <main className={styles.body}>
        {/* Services and Actions Cards (2 cards) */}
        <ServicesCard services={profileData.services} />
        <ActionsCard actions={profileData.availableActions} />

        {/* Messages and Posts Cards (2 cards) */}
        <MessagesCard messages={profileData.messages} />
        <PostsCard posts={profileData.posts} />

        {/* Certificates Section */}
        <CertificatesSection
          certificates={profileData.certificates}
          learningProgress={profileData.learningProgress}
        />

        {/* Badges & Achievements */}
        <BadgesAchievements badges={profileData.badges} achievements={profileData.achievements} />
      </main>

      {/* Sidebar - Fixed 268px width */}
      <aside className={styles.footer}>
        <ProfileSidebar user={profileData} session={session} />
      </aside>
    </div>
  )
}
