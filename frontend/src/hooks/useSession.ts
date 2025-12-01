'use client'

import { useEffect, useRef, useState } from 'react'

export interface SessionData {
  user?: {
    id: string
    webapp_user_id: string
    is_admin: boolean
    is_block: boolean
    telegram_user_id?: number | null
    camunda_user_id?: string | null
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

export interface UseSessionReturn {
  session: SessionData | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
}

/**
 * Client-side hook to access the current user session
 * Fetches session data from /api/auth/session endpoint
 *
 * Features:
 * - Automatically polls session when user is blocked (every 5s)
 * - Stops polling when user becomes unblocked
 * - Manual refetch via refetch() method
 */
export function useSession(): UseSessionReturn {
  const [session, setSession] = useState<SessionData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const previousSessionRef = useRef<string | null>(null)

  const fetchSession = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch('/api/auth/session', {
        credentials: 'include',
      })

      if (!response.ok) {
        throw new Error('Failed to fetch session')
      }

      const data = await response.json()

      // Only update session if the data actually changed
      const newSessionStr = JSON.stringify(data.session)
      if (previousSessionRef.current !== newSessionStr) {
        console.log('[useSession] Session data changed, updating state')
        previousSessionRef.current = newSessionStr
        setSession(data.session)
      } else {
        console.log('[useSession] Session data unchanged, skipping update')
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Unknown error'))
      setSession(null)
      previousSessionRef.current = null
    } finally {
      setLoading(false)
    }
  }

  // Initial fetch on mount
  useEffect(() => {
    fetchSession()
  }, [])

  // Auto-poll when user is blocked
  useEffect(() => {
    const isBlocked = session?.user?.is_block === true

    if (!isBlocked) {
      return
    }

    console.log('[useSession] User is blocked, starting auto-polling...')

    const interval = setInterval(() => {
      console.log('[useSession] Polling for unblock status...')
      fetchSession()
    }, 5000) // Poll every 5 seconds

    return () => {
      console.log('[useSession] User unblocked or unmounted, stopping polling')
      clearInterval(interval)
    }
  }, [session?.user?.is_block])

  return {
    session,
    loading,
    error,
    refetch: fetchSession,
  }
}
