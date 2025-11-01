'use client'

import { FC, ReactNode } from 'react'

import { VariablePayload } from '@/actions/engine'
import Loader from '@/components/atoms/Loader'
import {
  HistoricProcessInstanceEventEntity,
  useProcessInstanceWithWS,
} from '@/hooks/flow/useProcessInstanceWithWS'
import { components } from '@/services/flow/schema'

import { QuestTaskRunner } from './QuestTaskRunner'

import styles from './QuestRunner.module.scss'

type QuestInstanceRunnerProps = {
  className?: string
  instance: components['schemas']['ProcessInstanceSchema']
  onInstanceEnd?: (event: HistoricProcessInstanceEventEntity) => void
  onTaskOpen?: (id?: string) => void
  onTaskClose?: (id?: string) => void
  onTaskComplete?: (id?: string, variables?: Record<string, VariablePayload>) => void
  loader?: ReactNode
  taskKey?: string
  taskId?: string
  initialData?: {
    tasks?: components['schemas']['TaskSchema'][] | null
  }
}

export const QuestInstanceRunner: FC<QuestInstanceRunnerProps> = ({
  className,
  instance,
  onInstanceEnd,
  onTaskClose,
  onTaskComplete,
  loader,
  taskId,
  taskKey,
  initialData,
}) => {
  const { tasks, currentActivity } = useProcessInstanceWithWS({
    processInstanceId: instance.id,
    onProcessInstanceEnd: onInstanceEnd,
    query: {
      initialData: initialData?.tasks,
      refetchInterval: ({ state: { data } }) => (data?.length ? 30 : 5) * 1000,
    },
  })

  const activeTasks = tasks
    ?.filter(
      (x) =>
        x.state === 'ACTIVE' &&
        (!taskId || taskId === x.id) &&
        (!taskKey || taskKey === x.taskDefinitionKey)
    )
    ?.reverse()

  const task = activeTasks?.[0]

  if (!task) {
    if (currentActivity) {
      return <Loader className={styles.loader}>{currentActivity}</Loader>
    }

    return loader ?? <Loader className={styles.loader}>Waiting for tasks...</Loader>
  }

  return (
    <QuestTaskRunner
      className={className}
      instance={instance}
      task={task}
      onClose={onTaskClose}
      onComplete={onTaskComplete}
    />
  )
}
