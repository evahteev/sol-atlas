import { cookies } from 'next/headers'

import * as jose from 'jose'
import 'server-only'

import { SESSION_COOKIE_NAME } from '@/config/settings'

const SESSION_SECRET = new TextEncoder().encode(
  process.env.AUTH_SECRET || 'fallback-secret-key-min-32-chars-long'
)

export interface SessionPayload {
  userId: string
  webapp_user_id: string
  is_admin: boolean
  is_block: boolean
  telegram_user_id?: number | null
  camunda_user_id?: string | null
  expiresAt: Date
}

/**
 * Session type compatible with next-auth Session
 * Use this type instead of importing from 'next-auth'
 */
export interface Session {
  user?: {
    id: string
    webapp_user_id: string
    is_admin: boolean
    is_block: boolean
    is_suspicious?: boolean
    telegram_user_id?: number | null
    camunda_user_id?: string | null
    camunda_key?: string | null
    blofin_user_id?: string | number | null
    web3_wallets?: Array<{
      id: string
      address: string
      wallet_address?: string
      network_type?: string
      wallet_id?: string
    }>
    telegram_accounts?: Array<{
      id: string
      telegram_user_id: number
    }>
  }
  access_token?: string
  refresh_token?: string
  expires: string
}

/**
 * Convert SessionPayload to basic Session format
 * Note: This returns minimal session data. Use getSessionWithUser() for full user data.
 */
export function toSession(payload: SessionPayload): Session {
  return {
    user: {
      id: payload.userId,
      webapp_user_id: payload.webapp_user_id,
      is_admin: payload.is_admin,
      is_block: payload.is_block,
      telegram_user_id: payload.telegram_user_id,
      camunda_user_id: payload.camunda_user_id,
    },
    expires: payload.expiresAt.toISOString(),
  }
}

/**
 * Encrypt session data into a JWT
 */
export async function encrypt(payload: SessionPayload): Promise<string> {
  const jwt = await new jose.SignJWT({
    ...payload,
    expiresAt: payload.expiresAt.toISOString(),
  })
    .setExpirationTime('24h')
    .setProtectedHeader({ alg: 'HS256' })
    .sign(SESSION_SECRET)
  return jwt
}

/**
 * Decrypt and verify session JWT
 */
export async function decrypt(session: string | undefined = ''): Promise<SessionPayload | null> {
  if (!session) return null

  try {
    const { payload } = await jose.jwtVerify<SessionPayload>(session, SESSION_SECRET, {
      algorithms: ['HS256'],
    })

    return {
      userId: payload.userId,
      webapp_user_id: payload.webapp_user_id,
      is_admin: payload.is_admin,
      is_block: payload.is_block,
      telegram_user_id: payload.telegram_user_id,
      camunda_user_id: payload.camunda_user_id,
      expiresAt: new Date(payload.expiresAt),
    }
  } catch (error) {
    console.log('Failed to verify session:', error)
    return null
  }
}

/**
 * Create a new session cookie
 */
export async function createSession(
  userId: string,
  userData: Omit<SessionPayload, 'userId' | 'expiresAt'>
) {
  const expiresAt = new Date(Date.now() + 24 * 60 * 60 * 1000) // 24 hours
  const session = await encrypt({ ...userData, userId, expiresAt })

  const cookieStore = await cookies()
  cookieStore.set(SESSION_COOKIE_NAME, session, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    expires: expiresAt,
    sameSite: 'lax',
    path: '/',
  })
}

/**
 * Delete the session cookie
 */
export async function deleteSession() {
  const cookieStore = await cookies()
  cookieStore.delete(SESSION_COOKIE_NAME)
}

/**
 * Get the current session
 */
export async function getSession(): Promise<SessionPayload | null> {
  const cookieStore = await cookies()
  const session = cookieStore.get(SESSION_COOKIE_NAME)?.value
  return session ? await decrypt(session) : null
}

/**
 * Update/refresh the session with new expiration
 */
export async function updateSession() {
  const session = await getSession()
  if (!session) return null

  const expires = new Date(Date.now() + 24 * 60 * 60 * 1000)
  const refreshed = await encrypt({ ...session, expiresAt: expires })

  const cookieStore = await cookies()
  cookieStore.set(SESSION_COOKIE_NAME, refreshed, {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    expires,
    sameSite: 'lax',
    path: '/',
  })

  return session
}
