import { getFlowClient } from '@/services/flow/getClient'
import { components } from '@/services/flow/schema'

// User-related methods
export async function createUser(body: components['schemas']['Body_create_user_api_users_post']) {
  const client = getFlowClient()
  // always create user with is_block, they should be unblocked by /start command in tg bot
  const bodyWithBlock = { ...body, is_block: true }
  const { data, error } = await client.POST('/api/users', {
    body: bodyWithBlock,
  })
  if (error) {
    console.error('Error in createUser:', error)
    throw new Error('Error creating user')
  }
  return data
}

export async function getUser({
  telegram_user_id,
  webapp_user_id,
  user_id,
}: {
  user_id?: string
  webapp_user_id?: string
  telegram_user_id?: string
}) {
  if (!telegram_user_id && !webapp_user_id && !user_id) {
    throw new Error('getUser identifiers were not provided')
  }
  const client = getFlowClient()
  const params = { query: { telegram_user_id, webapp_user_id, user_id } }

  const { data, error } = await client.GET('/api/users', {
    params,
  })
  if (error) {
    console.error('Error in getUser:', error)
    throw new Error('Error getting user')
  }
  return data
}

export async function updateUser(body: components['schemas']['Body_update_user_api_users_put']) {
  const client = getFlowClient()

  const { data, error } = await client.PUT('/api/users', {
    body,
  })
  if (error) {
    console.error('Error in updateUser:', error)
    throw new Error('Error updaing user')
  }
  return data
}

export async function loginUser(webapp_user_id: string) {
  const client = getFlowClient()

  const params = { path: { webapp_user_id } }

  const { data, error } = await client.GET('/api/login/{webapp_user_id}', {
    params,
  })
  if (error) {
    console.error('Error in loginUser:', error)
    throw new Error('Error logging in')
  }
  return data
}

export async function refreshToken() {
  const client = getFlowClient()
  const { data, error } = await client.GET('/api/refresh')
  if (error) {
    console.error('Error in refreshToken:', error)
    throw new Error('Error refreshing token')
  }
  return data
}
