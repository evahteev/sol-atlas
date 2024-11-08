import { useQuery } from '@tanstack/react-query'

import { getProcessInstances } from '@/actions/engine'
import { FlowClientObject } from '@/services/flow'

import { components } from '../../schema'

const REFETCH_INTERVAL = 1000 // 1sec

export function useProcessDefinition(key: string) {
  return useQuery({
    queryKey: ['FlowClientObject.engine.process.definitions.get', key],
    queryFn: () => FlowClientObject.engine.process.definitions.get(key),
  })
}

export function useProcessInstances({
  businessKey = null,
  processDefinitionKey = null,
  initialData,
}: {
  businessKey?: string | null
  processDefinitionKey?: string | null
  initialData?: components['schemas']['ProcessInstanceSchema'][]
} = {}) {
  return useQuery({
    initialData,
    queryKey: [
      'FlowClientObject.engine.process.instance.list',
      { businessKey, processDefinitionKey }, // Include params in the queryKey for better caching
    ],
    queryFn: () => getProcessInstances({ businessKey, processDefinitionKey }),
    refetchInterval: REFETCH_INTERVAL, // Adjust this constant as needed
  })
}

export function useProcessInstanceTasks(
  processInstanceId?: string,
  schema?: components['schemas']['Body_filter_tasks_engine_task_post']['schema'],
  includeHistory = false
) {
  return useQuery({
    queryKey: ['FlowClientObject.engine.task.list', processInstanceId, schema, includeHistory],
    queryFn: async () => {
      if (!processInstanceId) {
        return null
      }
      const tasks = await FlowClientObject.engine.task.list(
        {
          ...schema,
          processInstanceId,
        },
        includeHistory
      )

      return tasks
    },
    refetchInterval: REFETCH_INTERVAL,
  })
}

export function useProcessInstanceVariables(
  instanceId: string | null,
  initialData?: { [key: string]: components['schemas']['VariableValueSchema'] } | null
) {
  return useQuery({
    initialData,
    queryKey: ['FlowClientObject.engine.process.instance.variables.list', instanceId],
    queryFn: async () => {
      if (!instanceId) {
        return null
      }
      try {
        const variables = await FlowClientObject.engine.process.instance.variables.list(instanceId)
        console.log('Fetched variables:', variables)
        return { ...variables }
      } catch (error: unknown) {
        if (error instanceof Error) {
          console.error('Error fetching process instance variables:', error.message)
        } else {
          console.error('Unknown error fetching process instance variables:', error)
        }
        return null
      }
    },
    refetchInterval: REFETCH_INTERVAL,
  })
}

export function useTasks(
  schema?: components['schemas']['Body_filter_tasks_engine_task_post']['schema'],
  includeHistory?: boolean,
  initialData?: components['schemas']['TaskSchema'][] | null
) {
  return useQuery({
    initialData,
    queryKey: ['FlowClientObject.engine.task.list', schema, includeHistory],
    queryFn: async () => {
      const tasks = await FlowClientObject.engine.task.list(schema, includeHistory)

      return tasks
    },
    refetchInterval: REFETCH_INTERVAL,
  })
}

export function useTaskVariables(taskId: string) {
  return useQuery({
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
