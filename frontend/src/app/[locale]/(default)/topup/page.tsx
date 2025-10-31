import Loader from '@/components/atoms/Loader'
import StateMessage from '@/components/composed/StateMessage'
import QuestRunner from '@/components/feature/QuestRunner'

import styles from './_assets/page.module.scss'

export default async function PageTopUp() {
  return (
    <div className={styles.container}>
      <QuestRunner
        processDefinitionKey="top_up_wallet"
        className={styles.body}
        isStartable
        content={{
          loader: <Loader className={styles.loader}>Warming up&hellip;</Loader>,
          starter: <Loader className={styles.loader}>Starting top up&hellip;</Loader>,
          waiting: <Loader className={styles.loader}>One moment&hellip;</Loader>,
          empty: (
            <StateMessage
              type="danger"
              className={styles.message}
              caption="Top up is not available at the moment."
            />
          ),
        }}
      />
    </div>
  )
}
