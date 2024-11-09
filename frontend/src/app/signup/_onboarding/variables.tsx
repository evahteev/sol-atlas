import { FC } from 'react'

import { Caption } from '@/components/ui'

import styles from '../_assets/page.module.scss'

export const OnboardingVariables: FC<{
  isPremium: boolean | null
  age: number | null
}> = ({ isPremium, age }) => {
  return (
    <div className={styles.results}>
      <Caption variant="header" size="lg">
        Results
      </Caption>

      <ul className={styles.resultsList}>
        {isPremium && (
          <li className={styles.resultsItem}>
            <div className={styles.result}>
              <Caption variant="header" size="md" className={styles.resultCaption}>
                Telegram Premium found
              </Caption>
              <span className={styles.resultCheck}></span>
              <span className={styles.resultProgress}></span>
            </div>
          </li>
        )}
        {age !== null && (
          <li className={styles.resultsItem}>
            <div className={styles.result}>
              <Caption variant="header" size="md" className={styles.resultCaption}>
                Account age: {age} years
              </Caption>
              <span className={styles.resultCheck}></span>
              <span className={styles.resultProgress}></span>
            </div>
          </li>
        )}
      </ul>
    </div>
  )
}
