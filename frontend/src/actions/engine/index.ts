'use server'

import { auth } from '@/auth'
import { getFlowClient } from '@/services/flow'
import { components, operations, paths } from '@/services/flow/schema'

export async function getProcessDefinitionList(
  query?: operations['get_process_definitions_engine_process_definition_get']['parameters']['query']
) {
  const client = getFlowClient({ useSysKey: true })

  const { data, error } = await client.GET('/engine/process-definition', {
    params: { query },
    next: {
      revalidate: 1 * 60,
      tags: ['all', 'flowClient', 'flowClientEngine', 'getProcessDefinitionList'],
    },
  })
  if (error) {
    console.error('Error in Engine Process Definition List:', error)
    throw new Error('Error in Engine Process Definition List')
  }
  return data
}

export async function getProcessDefinitionById(id: string) {
  try {
    return await getProcessDefinitionList({ processDefinitionId: id })
  } catch (error) {
    if (error) {
      console.error('Error in Engine Process Definition Get By Id:', error)
      throw new Error('Error in Engine Process Definition Get By Id')
    }
  }
}

export async function getProcessDefinitionByKey(key: string) {
  try {
    return await getProcessDefinitionList({ key })
  } catch (error) {
    if (error) {
      console.error('Error in Engine Process Definition Get By Key:', error)
      throw new Error('Error in Engine Process Definition Get By Key')
    }
  }
}

export async function startProcessInstanceByKey(
  key: string,
  body: components['schemas']['Body_start_process_instance_by_key_engine_process_definition_key__key__start_post']
) {
  const session = await auth()
  const client = getFlowClient()
  const businessKey = session?.user?.id

  if (!body.business_key) {
    body.business_key = businessKey
  }

  const { data, error } = await client.POST('/engine/process-definition/key/{key}/start', {
    params: { path: { key } },
    body,
    next: { revalidate: 10 * 60, tags: ['startProcessInstanceByKey'] },
  })
  if (error) {
    console.error('Error in startProcessInstanceByKey:', error)
    throw new Error('Error starting process by key')
  }
  return data
}

type GetProcessInstancesParams = paths['/engine/process-instance']['get']['parameters']['query']

export async function getProcessInstances({
  businessKey = null,
  processDefinitionKey = null,
}: {
  businessKey?: string | null
  processDefinitionKey?: string | null
} = {}) {
  const client = getFlowClient()

  // Initialize query parameters with the correct type
  const query: GetProcessInstancesParams = {}

  // Conditionally add parameters to the query object
  if (businessKey) {
    query.business_key = businessKey
  }
  if (processDefinitionKey) {
    query.process_definition_key = processDefinitionKey
  }

  const { data, error } = await client.GET('/engine/process-instance', {
    method: 'get',
    params: { query }, // Include the query in the params object
    next: { revalidate: 5, tags: ['getProcessInstances'] },
  })

  if (error) {
    console.error('Error in getProcessInstances:', error)
    throw new Error('Error getting process instances for user')
  }

  return data
}

export async function getProcessInstanceById(instance_id: string) {
  const client = getFlowClient()
  const { data, error } = await client.GET('/engine/process-instance/{instance_id}', {
    params: { path: { instance_id } },
    next: { revalidate: 5, tags: ['getProcessInstance'] },
  })
  if (error) {
    console.error('Error in getProcessInstance:', error)
    throw new Error('Error getting process instance for user')
  }
  return data
}

export async function getProcessInstanceVariables(instance_id: string) {
  const client = getFlowClient()
  const params = { path: { instance_id } }
  const { data, error } = await client.GET('/engine/process-instance/{instance_id}/variables', {
    params,
  })
  if (error) {
    console.error('Error in getProcessInstanceVariables:', error)
    throw new Error('Error getting process instance variables')
  }

  return data
}

export async function getTasks(
  schema?: components['schemas']['Body_filter_tasks_engine_task_post']['schema'],
  include_history = false
) {
  const client = getFlowClient()

  const { data, error } = await client.POST('/engine/task', {
    body: { schema, include_history },
  })
  if (error) {
    console.error('Error in getTasks:', error)
    throw new Error('Error getting tasks for user')
  }

  return data
}

export async function getProcessInstanceTasks({
  processInstanceId,
  ...schema
}: components['schemas']['Body_filter_tasks_engine_task_post']['schema'] & {
  processInstanceId: string
}) {
  return getTasks({ ...schema, processInstanceId })
}

export async function getTaskVariables(task_id: string) {
  const client = getFlowClient()

  const params = { path: { task_id } }
  const { data, error } = await client.GET('/engine/task/{task_id}/form-variables', { params })
  if (error) {
    console.error('Error in getTaskVariables:', error)
    throw new Error('Error getting process instance task form variables for user')
  }

  return data
}

export interface VariablePayload {
  valueInfo?: Record<string, object> | null
  type: string
  value: string | number | boolean | object
}

export async function completeTask(task_id: string, body?: Record<string, VariablePayload>) {
  const client = getFlowClient()
  const params = { path: { task_id } }

  // Ensure that the body is structured correctly, wrapping variables inside the "variables" key
  const formattedBody = {
    variables: body as Record<string, never>, // Type assertion to bypass the type check
  }

  const { data, error } = await client.POST('/engine/task/{task_id}/complete', {
    params,
    body: formattedBody,
  })
  if (error) {
    console.error('Error in completeTask:', error)
    throw new Error('Error completing task for user')
  }

  return data
}
