/* eslint-disable react-hooks/rules-of-hooks */
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import createClient, { type Middleware } from 'openapi-fetch'
import type { ParamsOption, RequestBodyOption } from 'openapi-fetch'

import { GET_PROCESS_INSTANCES } from '../flow/hooks'
import { paths } from './schema'

if (!process.env.CAMUNDA_URL) {
  throw new Error('Camunda engine api url is not defined')
}
const baseUrl = '/api/engine'

const CAMUNDA_USER = 'dexgurufe'
const CAMUNDA_PASSWORD = 'GAfcvz19piPIkpU'

const basicAuth: Middleware = {
  async onRequest(req) {
    req.headers.set('Authorization', `Basic ${btoa(`${CAMUNDA_USER}:${CAMUNDA_PASSWORD}`)}`)
    return req
  },
}

const throwOnError: Middleware = {
  async onResponse(res) {
    if (res.status >= 400) {
      const body = res.headers.get('content-type')?.includes('json')
        ? await res.clone().json()
        : await res.clone().text()
      throw new Error(body)
    }
    return undefined
  },
}

const client = createClient<paths>({ baseUrl })
client.use(basicAuth)
client.use(throwOnError)

export default client

type UseQueryOptions<T> = ParamsOption<T> &
  RequestBodyOption<T> & {
    // add your custom options here
    reactQuery?: {
      enabled: boolean // Note: React Query type’s inference is difficult to apply automatically, hence manual option passing here
      // add other React Query options as needed
    }
  }

export type UseMutationOptions<T> = ParamsOption<T> &
  RequestBodyOption<T> & {
    // add your custom options here
    reactQuery?: {
      enabled: boolean // Note: React Query type’s inference is difficult to apply automatically, hence manual option passing here
      // add other React Query options as needed
    }
  }

// paths
const GET_PROCESS_START_FORM = '/process-definition/key/{key}/form-variables'

export function getFlowStartForm({
  params,
  reactQuery,
}: UseQueryOptions<paths[typeof GET_PROCESS_START_FORM]['get']>) {
  return useQuery({
    ...reactQuery,
    queryKey: [GET_PROCESS_START_FORM, params],
    queryFn: async ({ signal }) => {
      const { data } = await client.GET(GET_PROCESS_START_FORM, {
        params,
        signal, // allows React Query to cancel request
      })
      return data
    },
  })
}

export const SUSPEND_PROCESS_INSTANCE = '/process-definition/{id}/suspended'
export function suspendProcessInstanceByKey() {
  return useMutation({
    mutationKey: [SUSPEND_PROCESS_INSTANCE],
    mutationFn: async ({
      params,
      body,
    }: UseMutationOptions<paths[typeof SUSPEND_PROCESS_INSTANCE]['put']>) => {
      const { data } = await client.PUT(SUSPEND_PROCESS_INSTANCE, {
        params,
        body,
      })
      return data
    },
    onSuccess: () => {
      // Invalidate and refetch
      const queryClient = useQueryClient()

      queryClient.invalidateQueries({ queryKey: [GET_PROCESS_INSTANCES] })
    },
  })
}

const GET_PROCESS_DEFINITION_XML = '/process-definition/key/{key}/xml'
export function useProcessDefinitionXml({
  params,
  reactQuery,
}: UseQueryOptions<paths[typeof GET_PROCESS_DEFINITION_XML]['get']>) {
  return useQuery({
    ...reactQuery,
    queryKey: [GET_PROCESS_DEFINITION_XML, params],
    queryFn: async ({ signal }) => {
      const { data } = await client.GET(GET_PROCESS_DEFINITION_XML, {
        params,
        signal, // allows React Query to cancel request
      })
      return data
    },
  })
}

const GET_PROCESS_DEFINITION = '/process-definition/key/{key}'
export function useProcessDefinition({
  params,
  reactQuery,
}: UseQueryOptions<paths[typeof GET_PROCESS_DEFINITION]['get']>) {
  return useQuery({
    ...reactQuery,
    queryKey: [GET_PROCESS_DEFINITION, params],
    queryFn: async ({ signal }) => {
      const { data } = await client.GET(GET_PROCESS_DEFINITION, {
        params,
        signal, // allows React Query to cancel request
      })
      return data
    },
  })
}

const GET_PROCESS_DEFINITION_START_FORM_VARIABLES = '/process-definition/key/{key}/form-variables'
export function useProcessDefinitionStartFormVariables({
  params,
  reactQuery,
}: UseQueryOptions<paths[typeof GET_PROCESS_DEFINITION_START_FORM_VARIABLES]['get']>) {
  return useQuery({
    ...reactQuery,
    queryKey: [GET_PROCESS_DEFINITION_START_FORM_VARIABLES, params],
    queryFn: async ({ signal }) => {
      const { data } = await client.GET(GET_PROCESS_DEFINITION_START_FORM_VARIABLES, {
        params,
        signal, // allows React Query to cancel request
      })
      return data
    },
  })
}
