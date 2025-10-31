import { useEffect, useState } from 'react'

import { QueryObserverOptions } from '@tanstack/react-query'
import uniqBy from 'lodash/uniqBy'
import { useSession } from 'next-auth/react'
import { env } from 'next-runtime-env'
import useWebSocket, { ReadyState } from 'react-use-websocket'

import { useTasks } from '@/services/flow/hooks/engine'
import { components } from '@/services/flow/schema'

// Basic interface for HistoryEvent common fields
// https://docs.camunda.org/javadoc/camunda-bpm-platform/7.19/org/camunda/bpm/engine/impl/history/event/HistoryEvent.html
interface HistoryEvent {
  caseDefinitionId: string | null
  caseDefinitionKey: string | null
  caseDefinitionName: string | null
  caseExecutionId: string | null
  caseInstanceId: string | null
  eventType: string | null
  executionId: string
  id: string | null
  processDefinitionId: string
  processDefinitionKey: string
  processDefinitionName: string
  processDefinitionVersion: string
  processInstanceId: string
  removalTime: number | null
  rootProcessInstanceId: string | null
  sequenceCounter: number | null
}
// https://docs.camunda.org/javadoc/camunda-bpm-platform/7.19/org/camunda/bpm/engine/impl/history/event/HistoricScopeInstanceEvent.html
interface HistoricScopeInstanceEvent extends HistoryEvent {
  durationInMillis: number | null
  endTime: number | null
  startTime: number | null
}

//https://docs.camunda.org/javadoc/camunda-bpm-platform/7.19/org/camunda/bpm/engine/impl/history/event/HistoricProcessInstanceEventEntity.html
export interface HistoricProcessInstanceEventEntity extends HistoricScopeInstanceEvent {
  businessKey: string
  deleteReason: string
  endActivityId: string
  startActivityId: string
  startUserId: string
  state: string | 'COMPLETED' | 'EXTERNALLY_TERMINATED'
  superCaseInstanceId: string
  superProcessInstanceId: string
  tenantId: string
}

// Historic Task Instance Event
// https://docs.camunda.org/javadoc/camunda-bpm-platform/7.19/org/camunda/bpm/engine/impl/history/event/HistoricTaskInstanceEventEntity.html
interface HistoricTaskInstanceEventEntity extends HistoricScopeInstanceEvent {
  activityInstanceId: string
  assignee: string | null
  deleteReason: string | null
  description: string | null
  dueDate: number | null
  followUpDate: number | null
  name: string
  owner: string | null
  parentTaskId: string | null
  priority: number
  taskDefinitionKey: string
  taskId: string
  tenantId: string
}

// Union type for filtering relevant events
type RelevantCamundaEvent = HistoricTaskInstanceEventEntity | HistoricProcessInstanceEventEntity

const isEndEvent = (message: HistoryEvent) =>
  Boolean((message as HistoricProcessInstanceEventEntity).endActivityId)

const isTaskEvent = (message: HistoryEvent) =>
  Boolean((message as HistoricTaskInstanceEventEntity).processInstanceId) &&
  Boolean((message as HistoricTaskInstanceEventEntity).taskId) &&
  Boolean((message as HistoricTaskInstanceEventEntity).activityInstanceId) &&
  Boolean((message as HistoricTaskInstanceEventEntity).taskDefinitionKey)

const mapTaskEventToTaskSchema = (
  event: HistoricTaskInstanceEventEntity
): components['schemas']['TaskSchema'] => {
  return {
    id: event.taskId,
    name: event.name,
    assignee: event.assignee,
    owner: event.owner,
    created: new Date(event.startTime ?? 0).toISOString(),
    due: event.dueDate ? new Date(event.dueDate).toISOString() : null,
    delegationState: null, // assuming no direct mapping, update if necessary
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
    suspended: false, // assuming no suspension info, set to default
    tenantId: event.tenantId,
    state: event.deleteReason === 'completed' ? 'COMPLETED' : 'ACTIVE',
  }
}

export const useProcessInstanceWithWS = ({
  processInstanceId,
  onProcessInstanceEnd,
  query,
  schema,
}: {
  processInstanceId: string
  onProcessInstanceEnd?: (event: HistoricProcessInstanceEventEntity) => void
  schema?: components['schemas']['Body_filter_tasks_engine_task_post']['schema']
  query?: Partial<QueryObserverOptions<components['schemas']['TaskSchema'][] | null | undefined>>
}) => {
  const NEXT_PUBLIC_WAREHOUSE_WS_API = env('NEXT_PUBLIC_WAREHOUSE_WS_API')
  const { data: session } = useSession()
  const [tasks, setTasks] = useState<components['schemas']['TaskSchema'][]>([])
  const [currentActivity, setCurrentActivity] = useState<string | null>()

  const { data: httpTasks } = useTasks({
    schema: {
      ...schema,
      processInstanceId: schema?.processInstanceBusinessKey ? undefined : processInstanceId,
    },
    includeHistory: true,
    session,
    query: {
      ...query,
      refetchInterval: query?.refetchInterval ?? 5 * 60 * 1000,
    },
  })

  const { lastJsonMessage, readyState } = useWebSocket<RelevantCamundaEvent>(
    `${NEXT_PUBLIC_WAREHOUSE_WS_API}/${processInstanceId}`,
    {
      retryOnError: true,
      share: true,
      shouldReconnect: () => true,
      reconnectInterval: 1000,
    }
  )

  useEffect(() => {
    if (!httpTasks?.length) {
      return
    }

    setTasks((currentTasks) => {
      const mergedTasks = uniqBy([...(currentTasks || []), ...httpTasks], 'id') // TODO: check if this is correct. possibly use only httpTasks
      return mergedTasks.sort(
        (a, b) => new Date(a.created).getTime() - new Date(b.created).getTime()
      )
    })
  }, [httpTasks])

  useEffect(() => {
    if (lastJsonMessage === null) {
      return
    }

    if (Object.hasOwn(lastJsonMessage, 'activityName')) {
      setCurrentActivity(
        lastJsonMessage.eventType !== 'end'
          ? (lastJsonMessage as { activityName?: string | null }).activityName
          : null
      )
    }

    if (isEndEvent(lastJsonMessage)) {
      const endMessage = lastJsonMessage as HistoricProcessInstanceEventEntity

      if (
        ['COMPLETED', 'EXTERNALLY_TERMINATED'].includes(endMessage.state) &&
        endMessage.processInstanceId === processInstanceId
      ) {
        console.log(`process instance has ended`, lastJsonMessage)
        onProcessInstanceEnd?.(endMessage)
      }
    }

    if (isTaskEvent(lastJsonMessage)) {
      const event = lastJsonMessage as HistoricTaskInstanceEventEntity
      const task = mapTaskEventToTaskSchema(event)
      const camundaUserId = session?.user?.camunda_user_id
      if (task.assignee !== camundaUserId) {
        return
      }

      setTasks((currentTasks) => {
        const currentTasksArray = [
          ...(currentTasks ?? []),
          ...(event.eventType === 'create' &&
          !currentTasks?.some((item) => item.id === event.taskId)
            ? [task]
            : []),
        ]
          .filter((item) => {
            const isDeleted = event.deleteReason === 'deleted'
            return !isDeleted || (isDeleted && item.id !== task.id)
          })
          .map((item) =>
            ['update', 'complete'].includes(event.eventType ?? '') && item.id === event.taskId
              ? task
              : item
          )

        return currentTasksArray
      })
    }
  }, [lastJsonMessage, session?.user?.camunda_user_id, onProcessInstanceEnd, processInstanceId])

  const connectionStatus = {
    [ReadyState.CONNECTING]: 'Connecting',
    [ReadyState.OPEN]: 'Open',
    [ReadyState.CLOSING]: 'Closing',
    [ReadyState.CLOSED]: 'Closed',
    [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
  }[readyState]

  return {
    currentActivity,
    tasks: tasks ?? [],
    lastJsonMessage,
    connectionStatus,
  }
}
