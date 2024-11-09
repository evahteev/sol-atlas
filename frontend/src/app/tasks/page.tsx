'use client'

import { Caption } from '@/components/ui'
import { questCustomRoute } from '@/config/custom'
import { useProcessInstances, useTasks } from '@/services/flow/hooks/engine'
import { useFlows } from '@/services/flow/hooks/flow'

import { Quest } from './_components/quest/Quest'

import styles from './_assets/page.module.scss'

export default function PageQuests() {
  const { data: flows, isLoading: isLoadingFlows } = useFlows()
  const { data: instances, isLoading: isLoadingInstances } = useProcessInstances()
  const { data: tasks, isLoading: isLoadingTasks } = useTasks(null, true)

  const isLoading = isLoadingFlows || isLoadingInstances || isLoadingTasks
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <Caption variant="header" size="lg">
          Quests
        </Caption>
      </div>

      <div className={styles.quests}>
        {flows?.map((quest) => {
          const questInstances = instances?.filter((instance) => {
            return instance.processDefinitionKey === quest.key
          })

          const questTasks = questInstances?.length
            ? questCustomRoute[quest.key]
              ? undefined
              : tasks
                  ?.filter((task) => {
                    return task.processDefinitionId === questInstances[0].processDefinitionId
                  })
                  .sort((a) => (a.state === 'COMPLETED' ? 1 : -1))
                  .reduce(
                    (acc, task) => {
                      if (!acc.find((item) => item.taskDefinitionKey === task.taskDefinitionKey)) {
                        acc.push(task)
                      }
                      return acc
                    },
                    [] as typeof tasks
                  )
            : undefined

          return (
            <Quest
              title={quest.name}
              description={quest.description ?? undefined}
              isDisabled={isLoading}
              key={quest?.id}
              id={quest.id}
              img={quest.img_picture}
              flowKey={quest.key}
              instances={questInstances}
              tasks={questTasks}
              reward={quest.reward}
            />
          )
        })}
      </div>
    </div>
  )
}
