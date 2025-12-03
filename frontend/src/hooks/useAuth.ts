import { useAutoConnect } from 'thirdweb/react'

import { thirdwebConnectBaseConfig } from '@/config/thirdweb'
import { useSession } from '@/hooks/useAuth.compat'

import { useConnectHandler } from './useConnectHandler'

type AuthData = {
  isAuth: boolean
  isLoading: boolean
}

/**
 * Custom authentication hook for Guru Network
 *
 * Authentication Flow:
 * 1. User connects wallet (Thirdweb) - wallet connection state
 * 2. useConnectHandler gets JWT and calls /api/auth/login
 * 3. Session cookie is created (gurunetwork_session)
 * 4. User is authenticated based on SESSION COOKIE (source of truth)
 *
 * IMPORTANT: We do NOT check wallet connection state for authentication.
 * - Wallet can be connected but user NOT authenticated (if login API failed)
 * - Session can exist but wallet disconnected (session persists)
 * - Session cookie is the ONLY source of truth for authentication
 *
 * @returns {AuthData} Authentication state based on session cookie
 */
export default function useAuth(): AuthData {
  const { status } = useSession()
  const { onConnectHandler } = useConnectHandler()

  // Auto-reconnect wallet on mount (does not affect auth state)
  // This only manages wallet connection, not authentication
  useAutoConnect({
    ...thirdwebConnectBaseConfig,
    onConnect: onConnectHandler,
    timeout: 10000,
  })

  // Authentication is based SOLELY on session state from cookie
  // Session cookie is created after: Thirdweb auth + Flow API login success
  const isLoading = status === 'loading'
  const isAuth = status === 'authenticated'

  return {
    isAuth,
    isLoading,
  }
}
