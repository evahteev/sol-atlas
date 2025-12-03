'use client'

import { usePathname, useRouter } from 'next/navigation'

import { FC, ReactNode, useCallback, useEffect, useState } from 'react'

import { useQueryClient } from '@tanstack/react-query'

import { VariablePayload } from '@/actions/engine'
import Loader from '@/components/atoms/Loader'
import RequireLogin from '@/components/composed/RequireLogin'
import StateMessage from '@/components/composed/StateMessage'
import { DEFAULT_REDIRECT_PATH } from '@/config/settings'
import { HistoricProcessInstanceEventEntity } from '@/hooks/flow/useProcessInstanceWithWS'
import { signOut, useSession } from '@/hooks/useAuth.compat'
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
  const router = useRouter()
  const pathname = usePathname()

  const { data: session, update } = useSession()
  const [currentInstance, setCurrentInstance] = useState(initialData?.instance)
  const [isCompleting, setIsCompleting] = useState(false)
  const [completingFlowName, setCompletingFlowName] = useState<string | null>(null)

  const { data: instances, isLoading } = useProcessInstances({
    businessKey: currentInstance?.businessKey || businessKey,
    processDefinitionKey,
    processInstanceIds: processInstanceId ? [processInstanceId] : null,
    session,
    query: {
      refetchInterval: ({ state: { data } }) => (data ? 30 : 5) * 1000,
    },
  })

  // Check if we're on a /flow/* route
  const isFlowRoute = pathname?.startsWith('/flow/')

  useEffect(() => {
    setCurrentInstance(initialData?.instance ?? null)
  }, [initialData?.instance])

  useEffect(() => {
    setCurrentInstance(instances?.[0] ?? null)
  }, [instances])

  const instance = currentInstance || instances?.[0]

  // Default completion handler for /flow/* routes
  const defaultFlowCompletionHandler = useCallback(
    async (event: HistoricProcessInstanceEventEntity) => {
      const flowName = instance?.processDefinitionName || instance?.processDefinitionKey || 'Flow'

      console.log('Flow completed:', event)
      setIsCompleting(true)
      setCompletingFlowName(flowName)

      try {
        // Refresh session to get updated user data from Flow API
        await update()

        // Wait for session to propagate
        setTimeout(() => {
          router.push(DEFAULT_REDIRECT_PATH)
        }, 500)
      } catch (error) {
        console.error('Error refreshing session after flow completion:', error)
        // On error, log out user and redirect
        await signOut({ redirect: false })
        router.push(DEFAULT_REDIRECT_PATH)
      }
    },
    [instance?.processDefinitionName, instance?.processDefinitionKey, update, router]
  )

  const handleInstanceEnd = useCallback(
    async (event: HistoricProcessInstanceEventEntity) => {
      // If on a /flow/* route and no custom handler, use default
      if (isFlowRoute && !onInstanceEnd) {
        await defaultFlowCompletionHandler(event)
      } else {
        onInstanceEnd?.(event)
      }
      setCurrentInstance(null)
    },
    [isFlowRoute, onInstanceEnd, defaultFlowCompletionHandler]
  )

  const handleTaskClose = useCallback(
    (taskId?: string) => {
      onTaskClose?.(taskId)
    },
    [onTaskClose]
  )

  const handleTaskComplete = useCallback(
    (taskId?: string) => {
      onTaskComplete?.(taskId)

      queryClient.invalidateQueries({
        queryKey: ['FlowClientObject.engine.task.list'],
      })
    },
    [onTaskComplete, queryClient]
  )

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

  // Show completion message while redirecting
  if (isCompleting && completingFlowName) {
    return (
      <Loader className={styles.loader}>
        Flow &ldquo;{completingFlowName}&rdquo; is completed, redirecting to {DEFAULT_REDIRECT_PATH}
        &hellip;
      </Loader>
    )
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
