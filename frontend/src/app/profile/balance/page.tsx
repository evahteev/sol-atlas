import { Caption, Card } from '@/components/ui'
import ImageLogo from '@/images/logo-guru.svg'

import { ProfileBalanceToken } from './_components/token'

import styles from '../_assets/page.module.scss'

export default async function PageProfileActivity() {
  return (
    <div className={styles.container}>
      <Card className={styles.disclaimer}>
        <ImageLogo className={styles.disclaimerIcon} />
        <Caption variant="body" size="md" className={styles.disclaimerTitle} strong>
          Disclaimer
        </Caption>{' '}
        <Caption variant="body" size="xs" className={styles.disclaimerText}>
          All balances & transactions actually on Guru Network testnet and doesn’t provide real
          value
        </Caption>
      </Card>

      <Caption variant="body" size="sm" className={styles.counter}>
        All 3 Tokens
      </Caption>

      <ul className={styles.list}>
        <li className={styles.item}>
          <ProfileBalanceToken image="https://placehold.co/160x160" burns={7493} />
        </li>
        <li className={styles.item}>
          <ProfileBalanceToken
            image="https://placehold.co/160x160"
            token={{ symbol: 'RBST', amount: 45000, value: 19, pnlDelta: 50 }}
          />
        </li>
        <li className={styles.item}>
          <ProfileBalanceToken
            image="https://placehold.co/160x160"
            token={{ symbol: 'PNDZ', amount: 23490, value: 16, pnlDelta: 23 }}
          />
        </li>
      </ul>
    </div>
  )
}
