import auth from '@/auth'
import StateMessage from '@/components/composed/StateMessage'
import QuestRunner from '@/components/feature/QuestRunner'
import Caption from '@/components/ui/Caption'
import { FlowClientObject } from '@/services/flow'

import styles from './_assets/page.module.scss'

type Params = Promise<{ instanceId: string }>

export default async function PageProcessInstance(props: { params: Params }) {
  const params = await props.params
  const instanceId = params.instanceId
  const session = await auth()
  const instance = session
    ? await FlowClientObject.engine.process.instance.get({ instanceId, session })
    : undefined

  if (!instance?.processDefinitionKey) {
    return (
      <StateMessage
        type="danger"
        className={styles.error}
        caption={
          <>
            No process instance <code>{instanceId}</code> found
          </>
        }
      />
    )
  }

  const flow = (await FlowClientObject.flows.list()).find(
    (x) => x.key === instance.processDefinitionKey
  )

  return (
    <>
      <div className={styles.header}>
        <Caption variant="header" size="lg" strong className={styles.title}>
          {flow?.name || instance.processDefinitionKey}
        </Caption>
        <Caption variant="header" size="xs" className={styles.subtitle}>
          {flow?.description}
        </Caption>
      </div>

      <QuestRunner
        processDefinitionKey={instance.processDefinitionKey}
        processInstanceId={instanceId}
        className={styles.task}
        initialData={{ instance }}
        content={{
          empty: (
            <StateMessage
              type="danger"
              className={styles.error}
              caption={
                <>
                  No process instance <code>{instanceId}</code> found
                </>
              }
            />
          ),
        }}
      />
    </>
  )
}
