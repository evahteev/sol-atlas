import { type User } from '@prisma/client'
import { decode } from 'jsonwebtoken'
import { getSession } from 'next-auth/react'
import createClient, { type Middleware } from 'openapi-fetch'

import { LocalStorageKeyEnum } from '@/config/settings'
import { ArtModel } from '@/models/art'
import { FlowModel } from '@/models/flow'

import { components, paths } from './schema'

const UNPROTECTED_ROUTES = ['/api/users', '/api/login']
if (!process.env.BOT_URL) {
  throw new Error('Flow api url is not defined')
}
const baseUrl = process.env.BOT_URL

async function fetchAccessToken(baseUrl: string) {
  try {
    const session = await getSession()
    if (!session) {
      throw new Error('User session not found')
    }
    const {
      user: { id },
    } = session as unknown as { user: User }
    const res = await fetch(`${baseUrl}/api/login/${id}`, { cache: 'no-cache' })
    if (res.status >= 400) {
      if (res.status === 401) {
        await fetchAccessToken(baseUrl)
      }
      const body = res.headers.get('content-type')?.includes('json')
        ? await res.clone().json()
        : await res.clone().text()
      throw new Error(JSON.stringify(body))
    }
    if (res.ok) {
      const { access_token, refresh_token } = await res.json()
      if (typeof window !== 'undefined') {
        localStorage.setItem(LocalStorageKeyEnum.access_token, access_token)
        localStorage.setItem(LocalStorageKeyEnum.refresh_token, refresh_token)
      }
      return access_token
    }
    return null
  } catch (e) {
    console.error(e)
  }
}

export const GET_INVITES_BY_CHAIN = '/api/invites/chain/{chain_id}'
export const GET_INVITES_BY_CHAIN_AND_TOKEN = '/api/invites/chain/{chain_id}/token/{token_id}'
export const GET_PROCESS_INSTANCE_TASK_VARIABLES = '/engine/task/{task_id}/form-variables'
export const COMPLETE_PROCESS_INSTANCE_TASK = '/engine/task/{task_id}/complete'
export const GET_ART_BY_ID = '/api/art/{art_id}'
export const POST_ART_LIKE = '/api/art/{art_id}/like'
export const GET_COLLECTION_BY_ID = '/api/art_collection/{collection_id}'

class FlowClient {
  private readonly client: ReturnType<typeof createClient<paths>>

  constructor(props?: { isServer?: boolean }) {
    const authMiddleware: Middleware = {
      async onRequest(req) {
        if (UNPROTECTED_ROUTES.some((pathname) => req.url.includes(pathname))) {
          return undefined // don’t modify request for certain paths
        }

        if (props?.isServer) {
          req.headers.set('x-sys-key', process.env.SYS_KEY ?? '')
          return req
        }

        let accessToken =
          typeof window !== 'undefined'
            ? localStorage.getItem(LocalStorageKeyEnum.access_token)
            : null

        if (accessToken) {
          const decoded = decode(accessToken) as { exp: number; webapp_user_id: string }
          const now = new Date().valueOf()
          const exp = decoded?.exp ?? 0
          if (exp * 1000 < now) {
            console.error('jwt expired!')
            accessToken = await fetchAccessToken(baseUrl)
          }
        } else {
          accessToken = await fetchAccessToken(baseUrl)
        }

        if (accessToken) {
          req.headers.set('Authorization', `Bearer ${accessToken}`)
          return req
        }
      },
      async onResponse(res) {
        if (res.status >= 400) {
          if (res.status === 401) {
            await fetchAccessToken(baseUrl)
          }
          const body = res.headers.get('content-type')?.includes('json')
            ? await res.clone().json()
            : await res.clone().text()
          throw new Error(JSON.stringify(body))
        }
        return undefined
      },
    }

    const client = createClient<paths>({ baseUrl })

    client.use(authMiddleware)

    this.client = client
  }
  // User-related methods
  async createUser(
    body: paths['/api/users']['post']['requestBody']['content']['application/json']
  ) {
    const { data, error } = await this.client.POST('/api/users', {
      body,
      headers: {
        'x-sys-key': process.env.SYS_KEY,
      },
    })
    if (error) {
      console.error('Error in createUser:', error)
      throw new Error('Error creating user')
    }
    return data
  }

  async loginUser(webapp_user_id: string) {
    const params = { path: { webapp_user_id } }

    const { data, error } = await this.client.GET('/api/login/{webapp_user_id}', {
      params,
    })
    if (error) {
      console.error('Error in loginUser:', error)
      throw new Error('Error logging in')
    }
    return data
  }

  async refreshToken() {
    const { data, error } = await this.client.GET('/api/refresh')
    if (error) {
      console.error('Error in refreshToken:', error)
      throw new Error('Error refreshing token')
    }
    return data
  }

  // External worker methods
  async getExternalWorkers(limit?: number, offset?: number) {
    const params = { query: { limit, offset } }
    const { data, error } = await this.client.GET('/api/external_workers', { params })
    if (error) {
      console.error('Error in getExternalWorkers:', error)
      throw new Error('Error fetching external workers')
    }
    return data
  }

  async createExternalWorker(
    body: paths['/api/external_workers']['post']['requestBody']['content']['application/json']
  ) {
    const { data, error } = await this.client.POST('/api/external_workers', {
      body,
      headers: {
        'Content-Type': 'application/json',
      },
    })
    if (error) {
      console.error('Error in createExternalWorker:', error)
      throw new Error('Error creating external worker')
    }
    return data
  }

  async getExternalWorkerById(externalWorkerId: string) {
    const params = { path: { external_worker_id: externalWorkerId } }
    const { data, error } = await this.client.GET('/api/external_workers/{external_worker_id}', {
      params,
    })
    if (error) {
      console.error('Error in getExternalWorkerById:', error)
      throw new Error('Error fetching external worker by ID')
    }
    return data
  }

  async updateExternalWorker(externalWorkerId: string) {
    const params = { path: { external_worker_id: externalWorkerId } }

    const { data, error } = await this.client.PUT('/api/external_workers/{external_worker_id}', {
      params,
    })
    if (error) {
      console.error('Error in updateExternalWorker:', error)
      throw new Error('Error updating external worker')
    }
    return data
  }

  async deleteExternalWorker(externalWorkerId: string) {
    const params = { path: { external_worker_id: externalWorkerId } }

    const { data, error } = await this.client.DELETE(`/api/external_workers/{external_worker_id}`, {
      params,
    })
    if (error) {
      console.error('Error in deleteExternalWorker:', error)
      throw new Error('Error deleting external worker')
    }
    return data
  }

  // flow methods
  async getFlows(limit?: number, offset?: number): Promise<FlowModel[]> {
    const params = { query: { limit, offset } }
    const { data, error } = await this.client.GET('/api/flows', { params })
    if (error) {
      console.error('Error in getFlows:', error)
      throw new Error('Error fetching flows')
    }
    return data
  }

  async createFlow(body: paths['/api/flow']['post']['requestBody']['content']['application/json']) {
    const { data, error } = await this.client.POST('/api/flow', {
      body,
    })
    if (error) {
      console.error('Error in createFlow:', error)
      throw new Error('Error creating flow')
    }
    return data
  }

  async getFlowById(flowId: string) {
    const params = { path: { flow_id: flowId } }
    const { data, error } = await this.client.GET(`/api/flow/{flow_id}`, { params })
    if (error) {
      console.error('Error in getFlowById:', error)
      throw new Error('Error fetching flow by ID')
    }
    return data
  }

  async updateFlow(flowId: string) {
    const params = { path: { flow_id: flowId } }

    const { data, error } = await this.client.PUT(`/api/flow/{flow_id}`, {
      params,
    })
    if (error) {
      console.error('Error in updateFlow:', error)
      throw new Error('Error updating flow')
    }
    return data
  }

  async deleteFlow(flowId: string) {
    const params = { path: { flow_id: flowId } }

    const { data, error } = await this.client.DELETE(`/api/flow/{flow_id}`, { params })
    if (error) {
      console.error('Error in deleteFlow:', error)
      throw new Error('Error deleting flow')
    }
    return data
  }

  async startProcessInstanceByKey(
    key: string,
    body: components['schemas']['Body_start_process_instance_by_key_engine_process_definition_key__key__start_post']
  ) {
    const session = await getSession()
    if (!session) {
      throw new Error('User session not found')
    }
    const {
      user: { id: businessKey },
    } = session as unknown as { user: User }

    const { data, error } = await this.client.POST('/engine/process-definition/key/{key}/start', {
      params: { path: { key } },
      body: { ...body, business_key: businessKey },
    })
    if (error) {
      console.error('Error in startProcessInstanceByKey:', error)
      throw new Error('Error starting process by key')
    }
    return data
  }

  async getProcessDefinition(flowKey: string) {
    const params = { query: { key: flowKey } }
    const { data, error } = await this.client.GET('/engine/process-definition', { params })
    if (error) {
      console.error('Error in getProcessDefinition:', error)
      throw new Error('Error getting process definition for user')
    }
    return data
  }

  async getProcessInstances(flowKey: string) {
    const params = { query: { processDefinitionKey: flowKey } }
    const { data, error } = await this.client.GET('/engine/process-instance', { params })
    if (error) {
      console.error('Error in getProcessInstances:', error)
      throw new Error('Error getting process instances for user')
    }
    return data
  }

  async getProcessInstanceVariables(instance_id: string) {
    const params = { path: { instance_id } }
    const { data, error } = await this.client.GET(
      '/engine/process-instance/{instance_id}/variables',
      {
        params,
      }
    )
    if (error) {
      console.error('Error in getProcessInstanceVariables:', error)
      throw new Error('Error getting process instance variables')
    }

    // TODO: change FE to work without this remap
    const variables: (components['schemas']['VariableValueSchema'] & { name: string })[] = []
    Object.keys(data).map((key) => {
      const variable: components['schemas']['VariableValueSchema'] & { name: string } = {
        name: key,
        value: data[key].value,
        type: data[key].type,
        valueInfo: data[key].valueInfo ?? {},
      } as const
      variables.push(variable)
    })
    return variables
  }

  async getProcessInstancesCount(flowKey: string) {
    const { data, error } = await this.client.GET('/engine/process-instance/count', {
      params: { query: { processDefinitionKey: flowKey } },
    })
    if (error) {
      console.error('Error in getProcessInstancesCount:', error)
      throw new Error('Error getting process instances count')
    }
    return data
  }

  async deleteProcessInstanceByKey(process_id: string) {
    const { data, error } = await this.client.DELETE('/engine/process-instance/{process_id}', {
      params: { path: { process_id } },
    })
    if (error) {
      console.error('Error in startProcessInstanceByKey:', error)
      throw new Error('Error starting process by key')
    }
    return data
  }

  async suspendProcessInstanceByKey(
    instance_id: string,
    body: paths['/engine/process-instance/{instance_id}/suspended']['put']['requestBody']['content']['application/json']
  ) {
    const { data, error } = await this.client.PUT(
      '/engine/process-instance/{instance_id}/suspended',
      {
        params: { path: { instance_id } },
        body,
      }
    )
    if (error) {
      console.error('Error in startProcessInstanceByKey:', error)
      throw new Error('Error starting process by key')
    }
    return data
  }

  async getProcessInstanceTasks(body: components['schemas']['Body_filter_tasks_engine_task_post']) {
    const { data, error } = await this.client.POST('/engine/task', { body })
    if (error) {
      console.error('Error in getProcessInstanceTasks:', error)
      throw new Error('Error getting process instance tasks for user')
    }
    return data
  }

  async getProcessInstanceTaskVariables(task_id: string) {
    const params = { path: { task_id } }
    const { data, error } = await this.client.GET(GET_PROCESS_INSTANCE_TASK_VARIABLES, { params })
    if (error) {
      console.error('Error in getProcessInstanceTaskVariables:', error)
      throw new Error('Error getting process instance task form variables for user')
    }
    return data
  }

  async completeProcessInstanceTask(
    task_id: string,
    // @ts-expect-error content here is nullable
    body?: paths['/engine/task/{task_id}/complete']['post']['requestBody']['content']['application/json']
  ) {
    const params = { path: { task_id } }
    const { data, error } = await this.client.POST(COMPLETE_PROCESS_INSTANCE_TASK, { params, body })
    if (error) {
      console.error('Error in completeProcessInstanceTask:', error)
      throw new Error('Error completing process instance task for user')
    }
    return data
  }

  async getInvites(chain_id: number, token_id: number) {
    const params = { path: { chain_id, token_id } }
    const { data, error } = await this.client.GET(GET_INVITES_BY_CHAIN_AND_TOKEN, { params })
    if (error) {
      console.error('Error in getInvites:', error)
      throw new Error('Error getting invites list')
    }
    return data
  }

  async postArtLike(art_id: string) {
    const params = { path: { art_id } }
    const { data, error } = await this.client.POST(POST_ART_LIKE, { params })
    if (error) {
      console.error('Error in postArtLike:', error)
      throw new Error('Error liking art by id')
    }

    return data
  }

  async getArtById(art_id: string) {
    const params = { path: { art_id } }
    const { data, error } = await this.client.GET(GET_ART_BY_ID, { params })
    if (error) {
      console.error('Error in getArtById:', error)
      throw new Error('Error getting art by id')
    }
    if (data.img_picture) {
      data.img_picture = data.img_picture.replace('s3://', 'https://')
    }
    return data
  }

  async getArts(limit?: number, offset?: number, type?: string): Promise<ArtModel[]> {
    const parameters = JSON.stringify({ type })
    const params = { query: { limit, offset, parameters } }
    const { data, error } = await this.client.GET('/api/arts', { params })
    if (error) {
      console.error('Error in getArts:', error)
      throw new Error('Error fetching arts')
    }
    return data
  }

  async getCollectionById(collection_id: string) {
    const params = { path: { collection_id } }
    const { data, error } = await this.client.GET(GET_COLLECTION_BY_ID, { params })
    if (error) {
      console.error('Error in getCollectionById:', error)
      throw new Error('Error getting collection by id')
    }
    return data
  }
}

export default FlowClient
