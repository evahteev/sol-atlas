'use client'

import { ReactNode, createContext, useContext } from 'react'

import { UseSessionReturn, useSession as useCustomSession } from '@/hooks/useSession'

// Create context for session management
const SessionContext = createContext<UseSessionReturn | null>(null)

/**
 * Hook to access session context
 * Must be used within SessionProvider
 */
export function useSessionContext(): UseSessionReturn {
  const context = useContext(SessionContext)

  if (!context) {
    throw new Error('useSessionContext must be used within SessionProvider')
  }

  return context
}

/**
 * SessionProvider component
 * Provides session state and refetch capability to all child components
 *
 * Features:
 * - Centralized session state management
 * - Automatic polling when user is blocked (handled by useSession)
 * - Manual refresh via update() method
 */
export function SessionProvider({ children }: { children: ReactNode }) {
  const sessionData = useCustomSession()

  return <SessionContext.Provider value={sessionData}>{children}</SessionContext.Provider>
}
