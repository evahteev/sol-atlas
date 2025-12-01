'use client'

/**
 * Compatibility wrapper for gradual migration from next-auth to custom session
 *
 * This provides a next-auth-like API using our custom session management.
 * Use this to maintain compatibility while migrating components.
 *
 * Eventually, components should use @/hooks/useSession directly.
 */
import type { Session } from '@/lib/session'
import { useSessionContext } from '@/providers/SessionProvider'

/**
 * Drop-in replacement for next-auth's useSession hook
 * Maps custom session to next-auth format for compatibility
 */
export function useSession() {
  const sessionContext = useSessionContext()

  const { session, loading, refetch } = sessionContext

  // Session already has the correct structure from API (Session type)
  return {
    data: session,
    status: loading ? 'loading' : session ? 'authenticated' : 'unauthenticated',
    update: async (data?: Partial<Session>) => {
      // If data is provided, call the update API to update session cookie
      // Otherwise, just refetch the current session
      if (data) {
        try {
          const response = await fetch('/api/auth/update', {
            method: 'PATCH',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(data),
            credentials: 'include',
          })

          if (response.ok) {
            const result = await response.json()
            // Refetch to get the updated session from the cookie
            await refetch()
            return result.session || sessionContext.session
          } else {
            console.error('Failed to update session:', await response.text())
            // Fall back to refetch
            await refetch()
            return sessionContext.session
          }
        } catch (error) {
          console.error('Session update error:', error)
          // Fall back to refetch on error
          await refetch()
          return sessionContext.session
        }
      } else {
        // No data provided, just refetch
        await refetch()
        return sessionContext.session
      }
    },
  }
}

/**
 * Compatibility signOut function
 * Calls new logout API
 *
 * Note: This function doesn't refresh session automatically.
 * If you need to clear session without redirect, call the update() method
 * from useSession() after calling signOut with redirect: false
 */
export async function signOut(options?: { redirect?: boolean; callbackUrl?: string }) {
  try {
    const response = await fetch('/api/auth/logout', {
      method: 'POST',
      credentials: 'include',
    })

    if (response.ok) {
      if (options?.redirect !== false) {
        window.location.href = options?.callbackUrl || '/login'
      }
      // If not redirecting, session will be cleared on next render
      // because the cookie has been removed
    } else {
      console.error('Logout failed')
    }
  } catch (error) {
    console.error('Logout error:', error)
  }
}

/**
 * Compatibility signIn function
 * Note: This is for credentials provider only
 * Thirdweb login should use /api/auth/login directly
 */
export async function signIn(
  provider: string,
  options?: {
    jwt?: string
    wallets?: string
    callbackUrl?: string
    redirect?: boolean
  }
) {
  if (provider !== 'credentials') {
    console.error('Only credentials provider is supported in custom session')
    return { error: 'Unsupported provider', ok: false }
  }

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        jwt: options?.jwt,
        wallets: options?.wallets ? JSON.parse(options.wallets) : [],
      }),
      credentials: 'include',
    })

    const data = await response.json()

    if (response.ok && data.success) {
      if (options?.redirect !== false && options?.callbackUrl) {
        window.location.href = options.callbackUrl
      }
      return { ok: true, error: null, status: 200, url: options?.callbackUrl }
    } else {
      return { ok: false, error: data.error || 'Login failed', status: response.status }
    }
  } catch (error) {
    console.error(error)
    return { ok: false, error: error, status: 500 }
  }
}

/**
 * SessionProvider component
 * Re-exported from @/providers/SessionProvider for compatibility
 */
export { SessionProvider } from '@/providers/SessionProvider'
