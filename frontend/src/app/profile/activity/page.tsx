import { Burns, Caption } from '@/components/ui'

import { ProfileActivityItem } from './_components/activity'

import styles from '../_assets/page.module.scss'

export default async function PageProfileActivity() {
  return (
    <div className={styles.container}>
      <Caption variant="body" size="sm" className={styles.counter}>
        23 New
      </Caption>

      <ul className={styles.list}>
        <li className={styles.item}>
          <ProfileActivityItem
            date={'2024-09-05 4:34:35'}
            tx="0x231f5fba9d2fa1c8c37ef10d5ed455862929587087d3561b8cfdd840da0ab82b">
            Booster won you got <Caption decorated="fire">45000</Caption> RBST on your balance
          </ProfileActivityItem>
        </li>
        <li className={styles.item}>
          <ProfileActivityItem
            date={'2024-09-05 4:34:35'}
            tx="0x231f5fba9d2fa1c8c37ef10d5ed455862929587087d3561b8cfdd840da0ab82b"
            image="https://placehold.co/48x48">
            You got <Burns>39322</Burns> votes for Pand zomby meme <Burns>-200</Burns>
          </ProfileActivityItem>
        </li>
        <li className={styles.item}>
          <ProfileActivityItem date={'2024-09-05 4:34:35'}>
            You purchased <Caption decorated="fire">23493</Caption> PNDZ for <Burns>20</Burns>
          </ProfileActivityItem>
        </li>
        <li className={styles.item}>
          <ProfileActivityItem date={'2024-09-05 4:34:35'}>
            You sold <Caption decorated="fire">23493</Caption> PNDZ for <Burns>20</Burns>
          </ProfileActivityItem>
        </li>
        <li className={styles.item}>
          <ProfileActivityItem date={'2024-09-05 4:34:35'} image="https://placehold.co/48x48">
            You created meme Robik (PMDS)
          </ProfileActivityItem>
        </li>
      </ul>
    </div>
  )
}
