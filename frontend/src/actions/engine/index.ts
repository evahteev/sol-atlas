import { TaskFormDeployedForm } from '@/components/composed/TaskForm/TaskFormDeployed/types'
import { Session } from '@/lib/session'
import { getFlowClient } from '@/services/flow/getClient'
import { components, operations, paths } from '@/services/flow/schema'

export async function getProcessDefinitionList(
  query?: operations['get_process_definitions_engine_process_definition_get']['parameters']['query']
) {
  const client = getFlowClient()

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
    return (await getProcessDefinitionList({ key }))?.[0]
  } catch (error) {
    if (error) {
      console.error('Error in Engine Process Definition Get By Key:', error)
      throw new Error('Error in Engine Process Definition Get By Key')
    }
  }
}

export async function deleteProcessInstanceById(id: string) {
  const client = getFlowClient()

  const { data, error } = await client.DELETE('/engine/process-instance/{process_id}', {
    params: { path: { process_id: id } },
  })
  if (error) {
    console.error('Error in startProcessInstanceByKey:', error)
    throw new Error('Error starting process by key')
  }
  return data
}

export async function startProcessInstanceByKey(
  key: string,
  body: components['schemas']['Body_start_process_instance_by_key_engine_process_definition_key__key__start_post'],
  session?: Session | null
) {
  const client = getFlowClient()
  const businessKey = session?.user?.id

  if (!body.business_key) {
    body.business_key = businessKey
  }

  const { data, error } = await client.POST('/engine/process-definition/key/{key}/start', {
    params: { path: { key } },
    body,
    headers: {
      Authorization: session?.access_token ? `Bearer ${session.access_token}` : undefined,
    },
    cache: 'no-cache',
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
  processInstanceIds = null,
  session,
}: {
  businessKey?: string | null
  processDefinitionKey?: string | null
  processInstanceIds?: string[] | null
  session?: Session | null
} = {}) {
  if (!session?.access_token) {
    return null
  }
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
  if (processInstanceIds) {
    query.process_instance_ids = processInstanceIds.join(',')
  }

  try {
    const { data, error } = await client.GET('/engine/process-instance', {
      params: { query }, // Include the query in the params object
      headers: {
        Authorization: `Bearer ${session.access_token}`,
      },
      cache: 'no-cache',
    })

    if (error) {
      console.error('Error in getProcessInstances:', error)
      return null
    }

    return data
  } catch (e) {
    if (e instanceof Error && e.message.includes('Not authenticated in flow API')) {
      return null
    }
    if (e instanceof Error && e.message.includes('Session not found in flow API')) {
      return null
    }
    console.error(e)
  }
}

export async function getProcessInstanceById({
  instanceId,
  session,
}: {
  instanceId: string
  session?: Session | null
}) {
  const client = getFlowClient()

  try {
    const { data, error } = await client.GET('/engine/process-instance/{instance_id}', {
      params: { path: { instance_id: instanceId } },
      next: { revalidate: 5, tags: ['getProcessInstance'] },
      headers: {
        Authorization: session?.access_token ? `Bearer ${session.access_token}` : undefined,
      },
    })
    if (error) {
      console.error('Error in getProcessInstance:', error)
      throw new Error('Error getting process instance for user')
    }
    return data
  } catch (e) {
    if (e instanceof Error && e.message.includes('Not authenticated in flow API')) {
      return null
    }
    if (e instanceof Error && e.message.includes('Session not found in flow API')) {
      return null
    }
    console.error(e)
  }
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

export async function getTasks({
  schema,
  include_history = false,
  session,
}: {
  schema?: components['schemas']['Body_filter_tasks_engine_task_post']['schema']
  include_history: boolean
  session?: Session | null
}) {
  const client = getFlowClient()
  try {
    const { data, error } = await client.POST('/engine/task', {
      body: { schema, include_history },
      headers: {
        Authorization: session?.access_token ? `Bearer ${session.access_token}` : undefined,
      },
      cache: 'no-cache',
    })
    if (error) {
      console.error('Error in getTasks:', error)
      throw new Error('Error getting tasks for user')
    }
    return data
  } catch (e) {
    if (e instanceof Error && e.message.includes('Session not found in flow API')) {
      return null
    }
  }
}

export async function getProcessInstanceTasks(
  { ...schema }: components['schemas']['Body_filter_tasks_engine_task_post']['schema'],
  include_history = false
) {
  return getTasks({ schema: { ...schema }, include_history })
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

export async function getTaskDeployedForm(task_id: string): Promise<TaskFormDeployedForm | null> {
  const client = getFlowClient()

  const params = { path: { task_id } }
  const { data, error } = await client.GET('/engine/task/{task_id}/deployed-form', { params })
  if (error) {
    console.error('Error in getTaskVariables:', error)
    throw new Error('Error getting process instance task form variables for user')
  }

  return (data as TaskFormDeployedForm) || null
}

export interface VariablePayload {
  valueInfo?: Record<string, object> | null
  type: string
  value: unknown
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

export async function proxyGet(full_path: string) {
  const client = getFlowClient()
  const params = { path: { full_path } }

  const { data, error } = await client.GET('/engine/proxy/{full_path}', { params })
  if (error) {
    console.error('Error in engine proxyGet:', error)
    throw new Error('Error getting engine proxy request')
  }

  return data
}

export async function proxyPut(full_path: string, body?: VariablePayload) {
  const client = getFlowClient()
  const params = { path: { full_path } }

  const { data, error } = await client.PUT('/engine/proxy/{full_path}', {
    params,
    // @ts-expect-error not ideal open api schema for proxy endpoint
    body,
  })
  if (error) {
    console.error('Error in engine proxyPut:', error)
    throw new Error('Error getting engine proxy PUT request')
  }

  return data
}
