import styles from '../_assets/page.module.scss'

export function ProfileBanner() {
  return (
    <div className={styles.utopiaPartnershipBanner}>
      <div className={styles.bannerContent}>
        <div className={styles.bannerIcon}>
          <span className={styles.rocketIcon}>🚀</span>
        </div>
        <div className={styles.bannerText}>
          <h2 className={styles.bannerTitle}>Utopia Partnership</h2>
          <p className={styles.bannerDescription}>
            Join the future of decentralized gaming and earn exclusive rewards through our
            partnership program.
          </p>
        </div>
        <div className={styles.bannerActions}>
          <button className={styles.learnMoreButton}>Learn More</button>
        </div>
      </div>
    </div>
  )
}
