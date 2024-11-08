'use server'

import { getFlowClient } from '@/services/flow'
import { operations } from '@/services/flow/schema'

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
