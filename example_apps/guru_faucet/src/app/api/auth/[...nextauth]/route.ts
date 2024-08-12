import type { NextRequest } from 'next/server'

import { handlers } from '@/app/auth'

// Referring to the auth.ts we just created
export const { POST } = handlers

export const GET = async (req: NextRequest): Promise<Response> => {
  const res = await handlers.GET(req)
  // for some reason next-auth /api/auth/* has default cache
  res.headers.set('Cache-Control', 'no-store, max-age=0, no-cache, must-revalidate')
  return res
}
