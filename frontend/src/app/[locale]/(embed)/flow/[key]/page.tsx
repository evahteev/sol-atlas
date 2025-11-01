import Loader from '@/components/atoms/Loader'
import StateMessage from '@/components/composed/StateMessage'
import QuestRunner from '@/components/feature/QuestRunner'

import styles from './_assets/page.module.scss'

type Params = {
  params: Promise<{ key: string }>
  searchParams: Promise<{ [key: string]: string | undefined }>
}

export const dynamic = 'force-dynamic'
export const fetchCache = 'force-no-store'

export default async function PageFlowsBySlug({ params, searchParams }: Params) {
  const key = (await params)?.key
  const queryParams = await searchParams
  const { variables, businessKey } = queryParams

  return (
    <div className={styles.container}>
      <QuestRunner
        processDefinitionKey={key}
        className={styles.body}
        startVariables={variables ? JSON.parse(variables) : undefined}
        businessKey={businessKey}
        isStartable
        content={{
          loader: <Loader className={styles.loader}>Preparing&hellip;</Loader>,
          starter: <Loader className={styles.loader}>Starting&hellip;</Loader>,
          waiting: <Loader className={styles.loader}>One moment&hellip;</Loader>,
          empty: (
            <StateMessage
              type="danger"
              className={styles.message}
              caption="Process is not available at the moment."
            />
          ),
        }}
      />
    </div>
  )
}
