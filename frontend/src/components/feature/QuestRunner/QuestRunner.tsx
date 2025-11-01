'use client'

import { FC, ReactNode, useEffect, useState } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import { useSession } from 'next-auth/react'

import { VariablePayload } from '@/actions/engine'
import Loader from '@/components/atoms/Loader'
import RequireLogin from '@/components/composed/RequireLogin'
import StateMessage from '@/components/composed/StateMessage'
import { HistoricProcessInstanceEventEntity } from '@/hooks/flow/useProcessInstanceWithWS'
import { useProcessInstances } from '@/services/flow/hooks/engine'
import { components } from '@/services/flow/schema'

import { QuestInstanceRunner } from './QuestInstanceRunner'
import { QuestInstanceStarter } from './QuestInstanceStarter'

import styles from './QuestRunner.module.scss'

export type QuestRunnerProps = {
  className?: string
  businessKey?: string
  processDefinitionKey?: string
  processInstanceId?: string
  initialData?: {
    instance?: components['schemas']['ProcessInstanceSchema'] | null
    tasks?: components['schemas']['TaskSchema'][] | null
  }
  startVariables?: {
    [key: string]: components['schemas']['VariableValueSchema']
  }
  taskKey?: string
  taskId?: string
  onInstanceEnd?: (event: HistoricProcessInstanceEventEntity) => void
  onInstanceStart?: (instance: components['schemas']['ProcessInstanceSchema']) => void
  onTaskClose?: (taskId?: string) => void
  onTaskComplete?: (taskId?: string, variables?: Record<string, VariablePayload>) => void
  isStartable?: boolean
  content?: {
    loader?: ReactNode
    starter?: ReactNode
    waiting?: ReactNode
    empty?: ReactNode
  }
}

export const QuestRunner: FC<QuestRunnerProps> = ({
  className,
  businessKey,
  processDefinitionKey,
  processInstanceId,
  initialData,
  startVariables,
  taskKey,
  taskId,
  onInstanceEnd,
  onInstanceStart,
  onTaskComplete,
  onTaskClose,
  isStartable,
  content: { loader, starter, empty, waiting } = {},
}) => {
  const queryClient = useQueryClient()

  const { data: session } = useSession()
  const [currentInstance, setCurrentInstance] = useState(initialData?.instance)
  const { data: instances, isLoading } = useProcessInstances({
    businessKey: currentInstance?.businessKey || businessKey,
    processDefinitionKey,
    processInstanceIds: processInstanceId ? [processInstanceId] : null,
    session,
    query: {
      refetchInterval: ({ state: { data } }) => (data ? 30 : 5) * 1000,
    },
  })

  useEffect(() => {
    setCurrentInstance(initialData?.instance ?? null)
  }, [initialData?.instance])

  useEffect(() => {
    setCurrentInstance(instances?.[0] ?? null)
  }, [instances])

  const instance = currentInstance || instances?.[0]

  if (!instance && isLoading) {
    return loader ?? <Loader className={styles.loader}>Loading instance&hellip;</Loader>
  }

  if (!instance) {
    if (!processDefinitionKey) {
      return (
        empty ?? (
          <StateMessage
            type="danger"
            className={styles.message}
            caption="No process definition key provided"
          />
        )
      )
    }

    if (isStartable) {
      return (
        <QuestInstanceStarter
          className={className}
          processDefinitionKey={processDefinitionKey}
          startVariables={startVariables}
          session={session}
          loader={starter}
          onInstanceStart={(instance) => {
            const newInstance = { ...instance, processDefinitionKey }
            setCurrentInstance(newInstance)
            onInstanceStart?.(newInstance)
          }}
        />
      )
    }

    return (
      empty ?? (
        <StateMessage
          type="danger"
          className={styles.message}
          caption={
            <>
              No instances found for <code>{processDefinitionKey}</code>
            </>
          }
        />
      )
    )
  }

  const handleInstanceEnd = (event: HistoricProcessInstanceEventEntity) => {
    onInstanceEnd?.(event)
    setCurrentInstance(null)
  }

  const handleTaskClose = (taskId?: string) => {
    onTaskClose?.(taskId)
  }

  const handleTaskComplete = (taskId?: string) => {
    onTaskComplete?.(taskId)

    queryClient.invalidateQueries({
      queryKey: ['FlowClientObject.engine.task.list'],
    })
  }

  return (
    <RequireLogin>
      <QuestInstanceRunner
        className={className}
        instance={instance}
        onInstanceEnd={handleInstanceEnd}
        onTaskClose={handleTaskClose}
        onTaskComplete={handleTaskComplete}
        loader={waiting}
        taskKey={taskKey}
        taskId={taskId}
        initialData={{ tasks: initialData?.tasks }}
      />
    </RequireLogin>
  )
}
