import { useEffect } from 'react'

import {
  QueryObserverOptions,
  keepPreviousData,
  useQuery,
  useQueryClient,
} from '@tanstack/react-query'
import { env } from 'next-runtime-env'

import { TaskFormDeployedForm } from '@/components/composed/TaskForm/TaskFormDeployed/types'
import { TaskFormVariable } from '@/components/composed/TaskForm/types'
import { TaskEvent, useTaskWebSocket } from '@/hooks/flow/useTaskWebSocket'
import { useSession } from '@/hooks/useAuth.compat'
import { Session } from '@/lib/session'
import { FlowClientObject } from '@/services/flow'

import { components } from '../../schema'

const REFETCH_INTERVAL = 1000 // 1sec

/**
 * Maps WebSocket TaskEvent to TaskSchema format for React Query cache
 * Based on architecture specification and existing useProcessInstanceWithWS pattern
 */
function mapTaskEventToTaskSchema(event: TaskEvent): components['schemas']['TaskSchema'] {
  return {
    id: event.taskId,
    name: event.name,
    assignee: event.assignee,
    owner: event.owner,
    created: event.startTime
      ? new Date(Number(event.startTime)).toISOString()
      : new Date().toISOString(),
    due: event.dueDate,
    lastUpdated: event.endTime
      ? new Date(Number(event.endTime)).toISOString()
      : new Date().toISOString(),
    delegationState: null,
    description: event.description,
    executionId: event.executionId,
    parentTaskId: event.parentTaskId,
    priority: event.priority,
    processDefinitionId: event.processDefinitionId,
    processInstanceId: event.processInstanceId,
    caseExecutionId: event.caseExecutionId,
    caseDefinitionId: event.caseDefinitionId,
    caseInstanceId: event.caseInstanceId,
    taskDefinitionKey: event.taskDefinitionKey,
    camundaFormRef: null,
    suspended: false,
    tenantId: event.tenantId,
    state: event.eventType === 'complete' ? 'COMPLETED' : 'ACTIVE',
  }
}

export function useProcessDefinition(
  key: string,
  query?: Partial<
    QueryObserverOptions<components['schemas']['ProcessDefinitionSchema'] | null | undefined>
  >
) {
  return useQuery({
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
    ...query,
    queryKey: ['FlowClientObject.engine.process.definitions.get', key],
    queryFn: () => FlowClientObject.engine.process.definitions.get(key),
  })
}

export function useProcessDefinitionStartFormVariables(
  key: string,
  query?: Partial<
    QueryObserverOptions<
      { [key: string]: components['schemas']['VariableValueSchema'] } | null | undefined
    >
  >
) {
  return useQuery({
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
    ...query,
    queryKey: ['FlowClientObject.engine.process.definitions.variables', key],
    queryFn: () => FlowClientObject.engine.process.definitions.variables(key),
  })
}

export function useProcessInstances({
  businessKey = null,
  processDefinitionKey = null,
  processInstanceIds = null,
  session,
  query,
}: {
  businessKey?: string | null
  processDefinitionKey?: string | null
  processInstanceIds?: string[] | null
  session?: Session | null
  query?: Partial<
    QueryObserverOptions<components['schemas']['ProcessInstanceSchema'][] | null | undefined>
  >
} = {}) {
  return useQuery({
    placeholderData: keepPreviousData,
    refetchInterval: REFETCH_INTERVAL, // Adjust this constant as needed
    ...query,
    queryKey: [
      'FlowClientObject.engine.process.instance-common',
      'FlowClientObject.engine.process.instance.list',
      { businessKey, processDefinitionKey, processInstanceIds, session }, // Include params in the queryKey for better caching
    ],
    queryFn: async () => {
      if (!session?.access_token) {
        return null
      }

      return FlowClientObject.engine.process.instance.list({
        businessKey,
        processDefinitionKey,
        processInstanceIds,
        session,
      })
    },
  })
}

export function useProcessInstance({
  id,
  session,
  query,
}: {
  id: string
  session?: Session | null
  query?: Partial<
    QueryObserverOptions<components['schemas']['ProcessInstanceSchema'] | null | undefined>
  >
}) {
  return useQuery({
    refetchInterval: 60 * 1000, // Adjust this constant as needed
    ...query,
    queryKey: [
      'FlowClientObject.engine.process.instance-common',
      'FlowClientObject.engine.process.instance.get',
      { id, session }, // Include params in the queryKey for better caching
    ],
    queryFn: async () => {
      if (!session?.access_token) {
        return null
      }
      return FlowClientObject.engine.process.instance.get({ instanceId: id, session })
    },
  })
}

export function useProcessInstanceTasks({
  processInstanceId,
  schema,
  includeHistory,
  query,
}: {
  processInstanceId?: string
  schema?: components['schemas']['Body_filter_tasks_engine_task_post']['schema']
  includeHistory: boolean
  query?: Partial<QueryObserverOptions<components['schemas']['TaskSchema'][] | null | undefined>>
}) {
  return useQuery({
    refetchInterval: REFETCH_INTERVAL,
    placeholderData: keepPreviousData,
    ...query,
    queryKey: ['FlowClientObject.engine.task.list', processInstanceId, schema, includeHistory],
    queryFn: async () => {
      if (!processInstanceId) {
        return null
      }
      const tasks = await FlowClientObject.engine.task.list({
        schema: {
          ...schema,
          processInstanceId,
        },
        include_history: includeHistory,
      })

      return tasks
    },
  })
}

export function useProcessInstanceVariables({
  instanceId,
  query,
}: {
  instanceId: string
  initialData?: { [key: string]: components['schemas']['VariableValueSchema'] } | null
  query?: Partial<
    QueryObserverOptions<
      { [key: string]: components['schemas']['VariableValueSchema'] } | null | undefined
    >
  >
}) {
  return useQuery({
    refetchInterval: REFETCH_INTERVAL,
    placeholderData: keepPreviousData,
    ...query,
    queryKey: [
      'FlowClientObject.engine.process.instance-common',
      'FlowClientObject.engine.process.instance.variables.list',
      instanceId,
    ],
    queryFn: async () => FlowClientObject.engine.process.instance.variables.list(instanceId),
  })
}

export function useTasks({
  schema,
  includeHistory = false,
  session,
  query,
}: {
  schema?: components['schemas']['Body_filter_tasks_engine_task_post']['schema']
  includeHistory?: boolean
  session?: Session | null
  query?: Partial<QueryObserverOptions<components['schemas']['TaskSchema'][] | null | undefined>>
}) {
  const queryClient = useQueryClient()
  const { data: currentSession } = useSession()

  // Feature flag for WebSocket (allows gradual rollout and easy rollback)
  const ENABLE_WEBSOCKET = env('NEXT_PUBLIC_ENABLE_TASK_WEBSOCKET') === 'true'

  // WebSocket integration for real-time task updates
  const { lastEvent, isConnected } = useTaskWebSocket({
    enabled: ENABLE_WEBSOCKET && !!session?.access_token,
  })

  // Dynamic polling interval based on WebSocket connection status
  // WebSocket connected: 5 minutes (fallback only)
  // WebSocket disconnected OR disabled: 1 second (primary updates)
  const refetchInterval = ENABLE_WEBSOCKET && isConnected ? 5 * 60 * 1000 : REFETCH_INTERVAL

  // Development logging
  if (process.env.NODE_ENV === 'development') {
    if (ENABLE_WEBSOCKET) {
      console.log(
        '[useTasks] WebSocket enabled, status:',
        isConnected ? 'connected' : 'disconnected'
      )
      console.log('[useTasks] Polling interval:', refetchInterval / 1000, 'seconds')
    } else {
      console.log('[useTasks] WebSocket disabled via feature flag, using HTTP polling only')
    }
  }

  // React Query for HTTP fetching
  const queryResult = useQuery({
    refetchInterval,
    placeholderData: keepPreviousData,
    ...query,
    queryKey: ['FlowClientObject.engine.task.list', schema, includeHistory, session],
    queryFn: async () => {
      if (!session?.access_token) {
        return null
      }
      return FlowClientObject.engine.task.list({ schema, include_history: includeHistory, session })
    },
  })

  // Process WebSocket events and update React Query cache
  useEffect(() => {
    if (!lastEvent || !currentSession?.user?.camunda_user_id) {
      return
    }

    // Development logging - WebSocket event received
    if (process.env.NODE_ENV === 'development') {
      console.log('[useTasks] WebSocket event received:', {
        type: lastEvent.eventType,
        taskId: lastEvent.taskId,
        taskName: lastEvent.name,
        assignee: lastEvent.assignee,
        processInstanceId: lastEvent.processInstanceId,
      })
    }

    // Filter: only process events for current user
    if (lastEvent.assignee !== currentSession.user.camunda_user_id) {
      if (process.env.NODE_ENV === 'development') {
        console.log('[useTasks] Event ignored - different user:', {
          eventAssignee: lastEvent.assignee,
          currentUser: currentSession.user.camunda_user_id,
        })
      }
      return
    }

    // Map WebSocket event to TaskSchema
    const task = mapTaskEventToTaskSchema(lastEvent)

    // Update React Query cache based on event type
    const queryKey = ['FlowClientObject.engine.task.list', schema, includeHistory, session]

    queryClient.setQueryData<components['schemas']['TaskSchema'][] | null>(queryKey, (oldData) => {
      if (!oldData) {
        return oldData
      }

      const oldCount = oldData.length
      let newData = oldData

      switch (lastEvent.eventType) {
        case 'create': {
          // Add new task if not already present (deduplication)
          if (oldData.some((t) => t.id === task.id)) {
            if (process.env.NODE_ENV === 'development') {
              console.log('[useTasks] Duplicate create event ignored:', task.id)
            }
            return oldData
          }
          // Add and sort by creation date (newest first)
          newData = [...oldData, task].sort(
            (a, b) => new Date(b.created).getTime() - new Date(a.created).getTime()
          )
          break
        }

        case 'update':
        case 'complete': {
          // Update existing task
          newData = oldData.map((t) => (t.id === task.id ? task : t))
          break
        }

        case 'delete': {
          // Remove task from list
          newData = oldData.filter((t) => t.id !== task.id)
          break
        }

        default:
          return oldData
      }

      // Development logging - Cache update summary
      if (process.env.NODE_ENV === 'development') {
        console.log('[useTasks] Cache updated:', {
          eventType: lastEvent.eventType,
          taskId: task.id,
          taskName: task.name,
          tasksCountBefore: oldCount,
          tasksCountAfter: newData.length,
        })
      }

      return newData
    })
  }, [
    lastEvent,
    currentSession?.user?.camunda_user_id,
    queryClient,
    schema,
    includeHistory,
    session,
  ])

  return queryResult
}

export function useTaskVariables(
  taskId: string,
  query?: Partial<
    QueryObserverOptions<
      { [key: string]: components['schemas']['VariableValueSchema'] } | null | undefined
    >
  >
) {
  return useQuery({
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
    staleTime: REFETCH_INTERVAL,
    ...query,
    queryKey: ['FlowClientObject.engine.task.variables.list', taskId],
    queryFn: async () => {
      if (!taskId) {
        throw new Error("taskId isn't defined")
      }
      const variables = await FlowClientObject.engine.task.variables.list(taskId)

      return variables
    },
  })
}

export function useTaskDeployedForm({
  taskId,
  instanceId,
  query,
}: {
  taskId: string
  instanceId: string
  query?: Partial<
    QueryObserverOptions<
      { form: TaskFormDeployedForm | null; variables: Record<string, TaskFormVariable> } | undefined
    >
  >
}) {
  return useQuery({
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
    staleTime: REFETCH_INTERVAL,
    ...query,
    queryKey: ['FlowClientObject.engine.task.form', taskId, instanceId],
    queryFn: async () => {
      if (!taskId) {
        throw new Error("taskId isn't defined")
      }
      const [deployedForm, formVariables] = await Promise.all([
        FlowClientObject.engine.task.form(taskId),
        FlowClientObject.engine.process.instance.variables.list(instanceId),
      ])
      return { form: deployedForm, variables: formVariables }
    },
  })
}

export function useDeployedStartForm({
  definitionKey,
  query,
}: {
  definitionKey: string
  query?: Partial<
    QueryObserverOptions<
      { form: TaskFormDeployedForm | null; variables: Record<string, TaskFormVariable> } | undefined
    >
  >
}) {
  return useQuery({
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
    ...query,
    queryKey: ['getVariables', definitionKey],
    queryFn: async () => {
      const form = await FlowClientObject.engine.process.definitions.form(definitionKey)
      return { form, variables: {} }
    },
  })
}

export function useStartFormVariables(
  definitionKey: string,
  query?: Partial<
    QueryObserverOptions<Record<string, components['schemas']['VariableValueSchema']>>
  >
) {
  return useQuery({
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
    retry: 1,
    ...query,
    queryKey: ['getVariables', definitionKey],
    queryFn: async () => FlowClientObject.engine.process.definitions.variables(definitionKey),
  })
}

export function useTaskFormVariables(
  taskId: string,
  query?: Partial<
    QueryObserverOptions<Record<string, components['schemas']['VariableValueSchema']>>
  >
) {
  return useQuery({
    refetchOnWindowFocus: false,
    placeholderData: keepPreviousData,
    ...query,
    queryKey: ['getVariables', taskId],
    queryFn: async () => FlowClientObject.engine.task.variables.list(taskId),
  })
}
