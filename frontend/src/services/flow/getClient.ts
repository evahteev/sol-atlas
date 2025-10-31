import { redirect } from 'next/navigation'

import { signIn } from 'next-auth/react'
import createClient, { type Middleware } from 'openapi-fetch'

import { paths } from './schema'

const authMiddleware = (): Middleware => {
  return {
    async onRequest(params) {
      return params.request
    },
    async onResponse(params) {
      if (params.response.status >= 400) {
        if (params.response.status === 401) {
          console.error('Unauthorized in FLOW API', JSON.stringify(params))
          if (typeof window !== 'undefined') {
            signIn()
          } else {
            redirect('/login')
          }
        }
        const body = params.response.headers.get('content-type')?.includes('json')
          ? await params.response.clone().json()
          : await params.response.clone().text()
        if (JSON.stringify(body).includes('Signature has expired')) {
          console.error('Signature has expired', JSON.stringify(params))
          if (typeof window !== 'undefined') {
            signIn()
          } else {
            redirect('/login')
          }
        }
        throw new Error(JSON.stringify(body))
      }
      return undefined
    },
  }
}

export const getFlowClient = () => {
  const nextjsServerOrigin = process.env.NEXTJS_SERVER_LOCAL_ORIGIN || 'https://localhost:3000'

  const client = createClient<paths>({
    baseUrl: `${typeof window === 'undefined' ? nextjsServerOrigin : window.location.origin}/api/flowapi`,
  })
  client.use(authMiddleware())

  return client
}
