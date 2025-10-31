'use client'

import { useState } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'

import Button from '@/components/ui/Button'
import Show from '@/components/ui/Show'
import { useProcessInstanceWithWS } from '@/hooks/flow/useProcessInstanceWithWS'
import { FlowClientObject } from '@/services/flow'
import { components } from '@/services/flow/schema'

import QuestStatus from '../QuestStatus'
import QuestTask from '../QuestTask'
import { QuestHistoryTask } from '../QuestTask/QuestHistoryTask'

import styles from './QuestInstance.module.scss'

type QuestInstanceProps = {
  className?: string
  flowKey: string
  img?: string | null
  instance: components['schemas']['ProcessInstanceSchema']
  tasks?: Awaited<ReturnType<typeof FlowClientObject.engine.task.list>>
  reward?: number
}

export function QuestInstance({
  className,
  flowKey,
  img,
  instance,
  reward,
  // tasks: httpTasks, TODO: initialData useQuery glitch
}: QuestInstanceProps) {
  const queryClient = useQueryClient()
  const [isExpanded, setIsExpanded] = useState(false)
  const processInstanceId = instance.id

  const { tasks, currentActivity } = useProcessInstanceWithWS({ processInstanceId })

  const handleComplete = () => {
    queryClient.invalidateQueries({
      queryKey: ['FlowClientObject.engine.task.list'],
    })
    queryClient.invalidateQueries({
      queryKey: ['FlowClientObject.engine.process.instance.list'],
    })

    if (reward) {
      queryClient.invalidateQueries({
        queryKey: ['balance'],
      })
    }
  }

  const handleExpand = () => {
    setIsExpanded(!isExpanded)
  }

  const filteredTasks = tasks.filter((item) => ['COMPLETED', 'ACTIVE'].includes(item.state ?? ''))
  const separatedStates = filteredTasks.reduce(
    (acc, curr) => {
      acc[curr.state ?? ''].push(curr)
      return acc
    },
    { COMPLETED: [], ACTIVE: [] } as Record<string, components['schemas']['TaskSchema'][]>
  )

  const collapsedTasks = [
    ...separatedStates.ACTIVE,
    ...(isExpanded
      ? separatedStates.COMPLETED
      : separatedStates.COMPLETED.slice(0, Math.min(separatedStates.COMPLETED.length, 3))),
  ]

  return (
    <>
      <div data-id={processInstanceId} className={clsx(className, styles.container)}>
        <Show if={currentActivity}>
          <QuestStatus
            message={currentActivity}
            className={styles.message}
            isLoading={!separatedStates.ACTIVE.length}
          />
        </Show>
        {collapsedTasks.map((task) => {
          if (task.state === 'COMPLETED') {
            return (
              <QuestHistoryTask
                key={task.id}
                title={task.name}
                description={task.description}
                className={styles.task}
              />
            )
          }

          if (task.state === 'ACTIVE') {
            return (
              <QuestTask
                task={task}
                icon={img}
                key={task.id}
                definitionKey={flowKey}
                onComplete={handleComplete}
                className={styles.task}
              />
            )
          }

          return null
        })}
      </div>

      <Show if={separatedStates.COMPLETED.length > 3}>
        <Button
          size="xxs"
          caption={`Show ${isExpanded ? 'less' : 'more'}`}
          className={clsx(styles.toggle, { [styles.expanded]: isExpanded })}
          onClick={handleExpand}
        />
      </Show>
    </>
  )
}
