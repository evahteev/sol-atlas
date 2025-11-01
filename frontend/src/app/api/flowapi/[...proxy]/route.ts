import { NextRequest, NextResponse } from 'next/server'

import auth from '@/auth'

const baseUrl = process.env.FLOW_API_URL

async function handler(originRequest: NextRequest) {
  const path = originRequest.url.split('/api/flowapi')[1] // take the original path with query params
  const url = `${baseUrl}${path}` // replace with target flowapi url

  const headers = new Headers(originRequest.headers)
  headers.delete('host') // Remove 'host' to avoid cross-origin issues
  headers.delete('transfer-encoding') // Prevents chunked transfer encoding issues

  const session = await auth()
  if (session?.access_token) {
    console.log('Request with Token to: ', url)
    headers.set('Authorization', `Bearer ${session.access_token}`)
  } else {
    console.log('Fallback Request with SYS_KEY to: ', url)
    headers.set('x-sys-key', process.env.FLOW_API_SYS_KEY ?? '')
  }

  const res = await fetch(url, {
    headers,
    method: originRequest.method,
    body: ['GET', 'HEAD'].includes(originRequest.method) ? null : originRequest.body, // Pass the original body directly
    redirect: 'manual', // Prevents automatic redirects
    duplex: 'half',
    cache: 'no-store', // need to get always fresh process-instance, user task and variables
  } as RequestInit)
  const body = res.headers.get('content-type')?.includes('json')
    ? await res
        .clone()
        .json()
        .catch((e) => {
          console.error(`Response parse error for ${url}`, e)
          return res.clone().text()
        })
    : await res.clone().text()

  if (!res.ok) {
    console.error(`Something went wrong in ${url}: ${res.status}. ${JSON.stringify(body)}`)
  }

  // Stream the response back without modifying it
  return new NextResponse(res.body, {
    status: res.status,
    headers: res.headers,
  })
}

export const dynamic = 'force-dynamic'

export { handler as GET, handler as POST, handler as DELETE, handler as PUT }
