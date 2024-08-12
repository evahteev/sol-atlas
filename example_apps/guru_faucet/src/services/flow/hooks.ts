/* eslint-disable react-hooks/rules-of-hooks */
import { useQuery } from '@tanstack/react-query'

import { getProcessDefinition } from '@/actions/engine'

import FlowClient, { GET_PROCESS_INSTANCE_TASK_VARIABLES } from './client'

const REFETCH_INTERVAL = 1000 // 1sec
// paths
export const GET_PROCESS_DEFINITION = '/engine/process-definition'

export function useProcessDefinition(key: string) {
  return useQuery({
    queryKey: [GET_PROCESS_DEFINITION, key],
    queryFn: () => getProcessDefinition({ flowKey: key, isServer: false }),
  })
}

export const GET_PROCESS_INSTANCES = '/engine/process-instance'

export function useProcessInstances(key: string) {
  return useQuery({
    queryKey: [GET_PROCESS_INSTANCES, key],
    queryFn: async () => {
      const flowClient = new FlowClient()
      const flows = await flowClient.getProcessInstances(key)
      const instancesWithVariables = await Promise.all(
        flows.map(async (x) => {
          const variables = await flowClient.getProcessInstanceVariables(x.id)
          return { ...x, variables }
        })
      )

      return instancesWithVariables
    },
    refetchInterval: REFETCH_INTERVAL,
  })
}

export function useProcessInstancesWithoutVariables(key: string) {
  return useQuery({
    queryKey: [GET_PROCESS_INSTANCES, key],
    queryFn: async () => {
      const flowClient = new FlowClient()
      const processInstances = await flowClient.getProcessInstances(key)
      return processInstances
    },
    refetchInterval: REFETCH_INTERVAL,
  })
}

export const GET_PROCESS_INSTANCE_TASKS = '/engine/task'
export function useProcessInstanceTasks(processInstanceId?: string) {
  return useQuery({
    queryKey: [GET_PROCESS_INSTANCE_TASKS, processInstanceId],
    queryFn: async () => {
      if (!processInstanceId) {
        return null
      }
      const flowClient = new FlowClient()
      const tasks = await flowClient.getProcessInstanceTasks({
        schema: { processInstanceId },
      })

      return tasks
    },
    refetchInterval: REFETCH_INTERVAL,
  })
}

export function useProcessInstanceTaskVariables(taskId: string) {
  return useQuery({
    queryKey: [GET_PROCESS_INSTANCE_TASK_VARIABLES, taskId],
    queryFn: async () => {
      if (!taskId) {
        throw new Error("taskId isn't defined")
      }
      const flowClient = new FlowClient()
      const variables = await flowClient.getProcessInstanceTaskVariables(taskId)

      return variables
    },
    refetchInterval: REFETCH_INTERVAL,
  })
}
