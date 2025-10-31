import { TaskFormDeployedForm } from '@/components/composed/TaskForm/TaskFormDeployed/types'
import { getFlowClient } from '@/services/flow/getClient'
import { operations } from '@/services/flow/schema'

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
    return await getProcessDefinitionList({ key })
  } catch (error) {
    if (error) {
      console.error('Error in Engine Process Definition Get By Key:', error)
      throw new Error('Error in Engine Process Definition Get By Key')
    }
  }
}

export async function getProcessDefinitionStartFormVariables(definition_key: string) {
  const client = getFlowClient()

  const { data, error } = await client.GET(
    '/engine/process-definition/{definition_key}/form-variables',
    {
      params: { path: { definition_key } },
      next: {
        revalidate: 1 * 60,
        tags: ['all', 'flowClient', 'flowClientEngine', 'getProcessDefinitionStartFormVariables'],
      },
    }
  )
  if (error) {
    console.error('Error in Engine Process Definition Start Form Variables:', error)
    throw new Error('Error in Engine Process Definition Start Form Variables')
  }
  return data
}

export async function getProcessDefinitionDeployedStartForm(key: string) {
  const client = getFlowClient()

  const { data, error } = await client.GET(
    '/engine/process-definition/key/{key}/deployed-start-form',
    {
      params: { path: { key } },
      next: {
        revalidate: 1 * 60,
        tags: ['all', 'flowClient', 'flowClientEngine', 'getProcessDefinitionDeployedStartForm'],
      },
    }
  )
  if (error) {
    console.error('Error in Engine Process Definition Deployed Start Form Variables:', error)
    throw new Error('Error in Engine Process Definition Deployed Start Form Variables')
  }
  return (data as TaskFormDeployedForm) ?? null
}
