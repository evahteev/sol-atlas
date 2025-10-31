import { getFlowClient } from '@/services/flow/getClient'

export async function getLeaderBoardUsers(limit: number = 10) {
  const client = getFlowClient()

  const { data, error } = await client.GET('/api/leaderboard/users', {
    params: { query: { limit } },
  })
  if (error) {
    console.error('Error in get next art:', error)
    throw new Error('Error getting next art')
  }
  return data
}

export async function getLeaderBoardUser(wallet_address?: string) {
  if (!wallet_address) {
    return null
  }
  const client = getFlowClient()

  const { data, error } = await client.GET('/api/leaderboard/users/{wallet_address}', {
    params: { path: { wallet_address } },
  })
  if (error) {
    console.error('Error in get next art:', error)
    throw new Error('Error getting next art')
  }
  return data
}

export async function getLeaderBoardArts(limit: number = 10) {
  const client = getFlowClient()

  const { data, error } = await client.GET('/api/leaderboard/arts', {
    params: { query: { limit } },
  })
  if (error) {
    console.error('Error in get next art:', error)
    throw new Error('Error getting next art')
  }
  return data
}
