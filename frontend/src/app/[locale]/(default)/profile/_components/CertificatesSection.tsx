import { Certificate, LearningProgress } from '../_types/profile'

import styles from '../_assets/page.module.scss'

interface CertificatesSectionProps {
  certificates: Certificate[]
  learningProgress: LearningProgress[]
}

export function CertificatesSection({
  certificates: _certificates,
  learningProgress: _learningProgress,
}: CertificatesSectionProps) {
  return (
    <div className={styles.profileCard}>
      <h3 className={styles.profileTitle}>Obtaining certificates</h3>

      {/* Base level - completed */}
      <div className={styles.certificateItem}>
        <div className={styles.certificateIcon}>
          <span className={styles.checkIcon}>✅</span>
        </div>
        <div className={styles.certificateContent}>
          <div className={styles.certificateHeader}>
            <h4 className={styles.certificateTitle}>Base level</h4>
            <span className={styles.certificateStatus}>20% completed</span>
          </div>
          <div className={styles.progressBarContainer}>
            <div className={styles.progressBar}>
              <div className={styles.progressFill} style={{ width: '20%' }} />
            </div>
          </div>
        </div>
      </div>

      {/* Expert level - locked */}
      <div className={styles.certificateItem}>
        <div className={styles.certificateIcon}>
          <span className={styles.lockIcon}>🔒</span>
        </div>
        <div className={styles.certificateContent}>
          <div className={styles.certificateHeader}>
            <h4 className={styles.certificateTitle}>Expert level</h4>
            <span className={styles.certificateStatusLocked}>Locked</span>
          </div>
          <div className={styles.progressBarContainer}>
            <div className={styles.progressBar}>
              <div className={styles.progressFill} style={{ width: '0%' }} />
            </div>
          </div>
        </div>
      </div>

      {/* Continue learning button */}
      <div className={styles.certificateButtonSection}>
        <button className={styles.continueButton}>Continue learning</button>
      </div>
    </div>
  )
}
