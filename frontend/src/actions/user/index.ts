'use server'

import { auth } from '@/auth'
import { getFlowClient } from '@/services/flow'
import { components } from '@/services/flow/schema'

export const getSessionFromServer = async () => {
  const session = await auth()
  return session
}

// User-related methods
export const createUser = async (
  body: components['schemas']['Body_create_user_api_users_post']
) => {
  const client = getFlowClient({ useSysKey: true })

  const { data, error } = await client.POST('/api/users', {
    body,
  })
  if (error) {
    console.error('Error in createUser:', error)
    throw new Error('Error creating user')
  }
  return data
}

export const getUser = async (telegram_user_id: string) => {
  const client = getFlowClient({ useSysKey: true })
  const params = { query: { telegram_user_id } }

  const { data, error } = await client.GET('/api/users', {
    params,
  })
  if (error) {
    console.error('Error in getUser:', error)
    throw new Error('Error getting user')
  }
  return data
}

export const updateUser = async (body: components['schemas']['Body_update_user_api_users_put']) => {
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

export const loginUser = async (webapp_user_id: string) => {
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

export const refreshToken = async () => {
  const client = getFlowClient()
  const { data, error } = await client.GET('/api/refresh')
  if (error) {
    console.error('Error in refreshToken:', error)
    throw new Error('Error refreshing token')
  }
  return data
}
