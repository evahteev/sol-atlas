import { getFlowClient } from '@/services/flow/getClient'

export async function getFlows(props?: { limit?: number; offset?: number; filter?: string }) {
  const { limit = 50, offset = 0, filter } = props ?? {}
  const client = getFlowClient()
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
    .filter((item) => {
      if (!filter) {
        return true
      }

      const regEx = new RegExp(filter)
      return regEx.test(item.type)
    })
    .reverse()
    .sort((a, b) => (b.sort_priority || 0) - (a.sort_priority || 0))
}

export async function getFlowById(flowId: string) {
  const client = getFlowClient()
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
