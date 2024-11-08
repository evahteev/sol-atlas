'use server'

import { getFlowClient } from '@/services/flow'

export async function getArtById(art_id: string) {
  const client = getFlowClient({ useSysKey: true })

  const params = { path: { art_id } }
  const { data, error } = await client.GET('/api/arts/{art_id}', { params })
  if (error) {
    console.error('Error in refreshToken:', error)
    throw new Error('Error refreshing token')
  }
  if (data.img_picture) {
    data.img_picture = data.img_picture.replace('s3://', 'https://')
  }
  return data
}

export async function getArts(query: string = '') {
  const client = getFlowClient({ useSysKey: true })

  const { data, error } = await client.GET('/api/arts', {
    params: { query: { parameters: query } },
  })
  if (error) {
    console.error('Error in get arts:', error)
    throw new Error('Error getting arts')
  }
  return data
}

export async function getArtsNext(count?: number) {
  const client = getFlowClient({ useSysKey: true })

  const { data, error } = await client.GET('/api/arts/next', { params: { query: { count } } })
  if (error) {
    console.error('Error in get next art:', error)
    throw new Error('Error getting next art')
  }
  return data
}

export async function getArtsRecommended(count?: number) {
  const client = getFlowClient()

  const { data, error } = await client.GET('/api/arts/recommended', {
    params: { query: { count } },
  })
  if (error) {
    console.error('Error in get next art:', error)
    throw new Error('Error getting next art')
  }
  return data
}

export async function getArtFinances(token_addresses?: string[]) {
  if (!token_addresses?.length) {
    return null
  }
  const client = getFlowClient({ useSysKey: true })

  const { data, error } = await client.GET('/api/finance/arts', {
    params: { query: { token_addresses: token_addresses.join(',') } },
  })
  if (error) {
    console.error('Error in get next art:', error)
    throw new Error('Error getting next art')
  }
  return data
}

export async function getCollectionById(collection_id: string) {
  if (!collection_id) {
    return null
  }
  const client = getFlowClient({ useSysKey: true })

  const params = { path: { collection_id } }
  const { data, error } = await client.GET('/api/art_collection/{collection_id}', { params })
  if (error) {
    console.error('Error in getCollectionById:', error)
    throw new Error('Error getting collection by id')
  }
  return data
}
