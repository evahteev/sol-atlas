import 'server-only'
import { cache } from 'react'
import { redirect } from 'next/navigation'
import { cookies } from 'next/headers'

import { getSession as getSessionFromCookie, Session, toSession, encrypt, SessionPayload } from '@/lib/session'
import { THIRDWEB_JWT_COOKIE_NAME, SESSION_COOKIE_NAME } from '@/config/settings'
import { FlowClientObject } from '@/services/flow'

/**
 * Get the current session (may be null)
 * Re-exported for compatibility
 */
export { getSession } from '@/lib/session'

/**
 * Get the session with full user data from Flow API and access token
 * This provides a complete Session object compatible with the old next-auth structure
 *
 * IMPORTANT: NOT cached - always fetches fresh user data from Flow API
 * This ensures is_block and other user status fields are always up-to-date
 */
export async function getSessionWithUser(): Promise<Session | null> {
  const sessionPayload = await getSessionFromCookie()
  if (!sessionPayload) return null

  try {
    // Get full user data from Flow API (always fresh, not cached)
    const user = await FlowClientObject.user.get({
      webapp_user_id: sessionPayload.webapp_user_id,
    })

    // Get access token from Thirdweb JWT cookie
    const cookieStore = await cookies()
    const thirdwebJWT = cookieStore.get(THIRDWEB_JWT_COOKIE_NAME)?.value

    // Build complete session object
    // IMPORTANT: Use is_block from Flow API user data, NOT from session cookie
    // This ensures we always have the latest block status
    return {
      user: {
        id: sessionPayload.userId,
        webapp_user_id: sessionPayload.webapp_user_id,
        is_admin: user?.is_admin ?? sessionPayload.is_admin,
        is_block: user?.is_block ?? sessionPayload.is_block, // Prefer Flow API value
        telegram_user_id: sessionPayload.telegram_user_id,
        camunda_user_id: sessionPayload.camunda_user_id,
        web3_wallets: user?.web3_wallets?.map((w: any) => ({
          id: String(w.id),
          address: w.wallet_address || w.address,
          wallet_address: w.wallet_address,
          network_type: w.network_type,
          wallet_id: w.wallet_id,
        })) || [],
        telegram_accounts: user?.telegram_accounts?.map((t: any) => ({
          id: String(t.id),
          telegram_user_id: t.telegram_id || t.telegram_user_id,
        })) || [],
      },
      access_token: thirdwebJWT,
      expires: sessionPayload.expiresAt.toISOString(),
    }
  } catch (error) {
    console.error('Failed to fetch user for session:', error)
    // Return basic session without full user data
    const cookieStore = await cookies()
    const thirdwebJWT = cookieStore.get(THIRDWEB_JWT_COOKIE_NAME)?.value

    return {
      ...toSession(sessionPayload),
      access_token: thirdwebJWT,
    }
  }
}

/**
 * Verify the user session and return session data
 * Redirects to /login if no valid session exists
 * Uses React cache to prevent redundant session checks
 */
export const verifySession = cache(async () => {
  const session = await getSessionFromCookie()

  if (!session?.userId) {
    redirect('/login')
  }

  return { isAuth: true, ...session }
})

/**
 * Get the full user data from the Flow API
 * Uses React cache to prevent redundant API calls
 */
export const getUser = cache(async (): Promise<any | null> => {
  const session = await verifySession()

  try {
    const user = await FlowClientObject.user.get({
      webapp_user_id: session.webapp_user_id,
    })

    return user
  } catch (error) {
    console.error('Failed to fetch user:', error)
    return null
  }
})

/**
 * Get user by ID
 */
export const getUserById = cache(async (userId: string) => {
  try {
    const user = await FlowClientObject.user.get({
      user_id: userId,
    })

    return user
  } catch (error) {
    console.error('Failed to fetch user by ID:', error)
    return null
  }
})

/**
 * Update session cookie with partial data
 * Merges update data with existing session and re-encrypts
 * Returns the updated Session object with full user data
 */
export async function updateSessionData(updates: Partial<Session>): Promise<Session | null> {
  const currentSession = await getSessionFromCookie()

  if (!currentSession) {
    return null
  }

  try {
    // If user data is being updated, merge it with existing user data from Flow API
    let fullUserData = null
    if (updates.user) {
      // Fetch current user data from Flow API
      fullUserData = await FlowClientObject.user.get({
        webapp_user_id: currentSession.webapp_user_id,
      })
    }

    // Prepare updated session payload
    // Note: Session cookie only stores core fields, not web3_wallets
    // web3_wallets are stored in Flow API and must be updated there separately
    const updatedPayload: SessionPayload = {
      ...currentSession,
      // Keep core session fields - they don't change via this method
      userId: currentSession.userId,
      webapp_user_id: currentSession.webapp_user_id,
      is_admin: currentSession.is_admin,
      is_block: currentSession.is_block,
      telegram_user_id: currentSession.telegram_user_id,
      camunda_user_id: currentSession.camunda_user_id,
      expiresAt: new Date(Date.now() + 24 * 60 * 60 * 1000), // Refresh expiration
    }

    // Re-encrypt session with same data but refreshed expiration
    const encryptedSession = await encrypt(updatedPayload)

    // Update cookie
    const cookieStore = await cookies()
    cookieStore.set(SESSION_COOKIE_NAME, encryptedSession, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      expires: updatedPayload.expiresAt,
      sameSite: 'lax',
      path: '/',
    })

    // Return full session with updated user data from Flow API
    const cookieStore2 = await cookies()
    const thirdwebJWT = cookieStore2.get(THIRDWEB_JWT_COOKIE_NAME)?.value

    return {
      user: fullUserData ? {
        id: updatedPayload.userId,
        webapp_user_id: updatedPayload.webapp_user_id,
        is_admin: fullUserData.is_admin ?? updatedPayload.is_admin,
        is_block: fullUserData.is_block ?? updatedPayload.is_block,
        telegram_user_id: updatedPayload.telegram_user_id,
        camunda_user_id: updatedPayload.camunda_user_id,
        web3_wallets: fullUserData.web3_wallets?.map((w: any) => ({
          id: String(w.id),
          address: w.wallet_address || w.address,
          wallet_address: w.wallet_address,
          network_type: w.network_type,
          wallet_id: w.wallet_id,
        })) || [],
        telegram_accounts: fullUserData.telegram_accounts?.map((t: any) => ({
          id: String(t.id),
          telegram_user_id: t.telegram_id || t.telegram_user_id,
        })) || [],
      } : {
        id: updatedPayload.userId,
        webapp_user_id: updatedPayload.webapp_user_id,
        is_admin: updatedPayload.is_admin,
        is_block: updatedPayload.is_block,
        telegram_user_id: updatedPayload.telegram_user_id,
        camunda_user_id: updatedPayload.camunda_user_id,
      },
      access_token: thirdwebJWT,
      expires: updatedPayload.expiresAt.toISOString(),
    }
  } catch (error) {
    console.error('Failed to update session data:', error)
    return null
  }
}
