import AIChat from '@/components/feature/AIChat'

import styles from './_assets/page.module.scss'

export default async function PageAgents() {
  return <AIChat className={styles.chat} integrationId="luka" />
}
