'use server'

import { getFlowClient } from '@/services/flow'

export async function getFlows(props?: { limit?: number; offset?: number }) {
  const { limit = 30, offset = 0 } = props ?? {}
  const client = getFlowClient({ useSysKey: true })
  const params = { query: { limit, offset } }
  const { data, error } = await client.GET('/api/flows', {
    params,
    next: { revalidate: 10 * 60, tags: ['all', 'getFlows'] },
  })
  if (error) {
    console.error('Error in getFlows:', error)
    throw new Error('Error fetching flows')
  }
  return data
}

export async function getFlowById({ flowId }: { flowId: string }) {
  const client = getFlowClient({ useSysKey: true })
  const params = { path: { flow_id: flowId } }
  const { data, error } = await client.GET(`/api/flow/{flow_id}`, {
    params,
    next: {
      revalidate: 10 * 60,
      tags: ['all', 'getFlows'],
    },
  })
  if (error) {
    console.error('Error in getFlowById:', error)
    throw new Error('Error fetching flow by ID')
  }
  return data ?? null
}
