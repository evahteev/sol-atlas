import createClient, { type Middleware } from 'openapi-fetch'

import {
  getArtById,
  getArtFinances,
  getArts,
  getArtsNext,
  getArtsRecommended,
  getCollectionById,
} from '@/actions/arts'
import {
  completeTask,
  getProcessDefinitionByKey,
  getProcessDefinitionList,
  getProcessInstanceById,
  getProcessInstanceTasks,
  getProcessInstanceVariables,
  getProcessInstances,
  getTaskVariables,
  getTasks,
  startProcessInstanceByKey,
} from '@/actions/engine'
import { getFlowById, getFlows } from '@/actions/flows'
import { getLeaderBoardArts, getLeaderBoardUser, getLeaderBoardUsers } from '@/actions/leaderboard'
import { createUser, getUser, loginUser, refreshToken, updateUser } from '@/actions/user'
import { auth } from '@/auth'

import { paths } from './schema'

const UNPROTECTED_ROUTES = ['/api/users', '/api/login']

const baseUrl = process.env.FLOW_API_URL
console.log('FLOW_API_URL', baseUrl)

console.log('SYS_KEY', process.env.SYS_KEY)

type AuthMiddlewareProps = { useSysKey?: boolean }

const authMiddleware = (params?: AuthMiddlewareProps): Middleware => {
  const { useSysKey = false } = params ?? {}

  return {
    async onRequest(params) {
      if (
        useSysKey ||
        UNPROTECTED_ROUTES.some((pathname) => params.request.url.includes(pathname))
      ) {
        console.log('Request with SYS_KEY to: ', params.request.url)
        params.request.headers.set('x-sys-key', process.env.SYS_KEY ?? '')
        return params.request
      }

      const session = await auth()

      if (session?.access_token) {
        console.log('Request with Token to: ', params.request.url)
        params.request.headers.set('Authorization', `Bearer ${session.access_token}`)
        return params.request
      } else {
        throw Error(`Session not found in flow API ${JSON.stringify(params)}`)
      }
    },
    async onResponse(params) {
      if (params.response.status >= 400) {
        if (params.response.status === 401) {
          throw Error('Not authenticated in flow API')
        }
        const body = params.response.headers.get('content-type')?.includes('json')
          ? await params.response.clone().json()
          : await params.response.clone().text()
        throw new Error(JSON.stringify(body))
      }
      return undefined
    },
  }
}

export const getFlowClient = (params?: AuthMiddlewareProps) => {
  const client = createClient<paths>({ baseUrl })
  client.use(authMiddleware(params))

  return client
}

export const FlowClientObject = {
  flows: {
    list: getFlows,
    get: getFlowById,
  },
  user: {
    create: createUser,
    get: getUser,
    login: loginUser,
    update: updateUser,
    refreshToken: refreshToken,
  },
  engine: {
    process: {
      definitions: {
        list: getProcessDefinitionList,
        get: getProcessDefinitionByKey,
        start: startProcessInstanceByKey,
        variables: getProcessInstanceVariables,
      },
      instance: {
        list: getProcessInstances,
        get: getProcessInstanceById,
        task: {
          list: getProcessInstanceTasks,
        },
        variables: {
          list: getProcessInstanceVariables,
        },
      },
    },
    task: {
      list: getTasks,
      variables: {
        list: getTaskVariables,
      },
      complete: completeTask,
    },
  },
  arts: {
    get: getArtById,
    list: getArts,
    next: getArtsNext,
    recommended: getArtsRecommended,
    finances: getArtFinances,
    collection: getCollectionById,
  },
  leaderboard: {
    users: {
      list: getLeaderBoardUsers,
      get: getLeaderBoardUser,
    },
    arts: {
      list: getLeaderBoardArts,
    },
  },
}
