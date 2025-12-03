import { useMemo } from 'react'

import { env } from 'next-runtime-env'
import useWebSocket, { ReadyState } from 'react-use-websocket'

import { useSession } from '@/hooks/useSession'

/**
 * Task event from WebSocket endpoint /api/ws/tasks
 * Backend event format from Camunda history events
 */
export interface TaskEvent {
  // Event metadata
  eventType: 'create' | 'complete' | 'update' | 'delete'

  // Task identification
  id: string // Task ID
  taskId: string // Same as id
  taskDefinitionKey: string
  name: string // Task name
  description: string | null

  // Assignment
  assignee: string | null // camunda_user_id
  camundaUserId: string | null // Same as assignee
  owner: string | null

  // Process context
  processInstanceId: string
  processDefinitionId: string
  processDefinitionKey: string
  processDefinitionName: string | null
  processDefinitionVersion: number | null
  rootProcessInstanceId: string
  executionId: string
  activityInstanceId: string

  // Case management (optional)
  caseInstanceId: string | null
  caseExecutionId: string | null
  caseDefinitionId: string | null
  caseDefinitionKey: string | null
  caseDefinitionName: string | null

  // Task metadata
  priority: number
  parentTaskId: string | null
  deleteReason: string | null

  // Timing
  startTime: number | null
  endTime: number | null
  dueDate: string | null
  followUpDate: string | null
  durationInMillis: number | null
  removalTime: string | null

  // Misc
  tenantId: string | null
  sequenceCounter: number
}

/**
 * Connection status enum matching ReadyState from react-use-websocket
 */
export type ConnectionStatus = 'Uninstantiated' | 'Connecting' | 'Open' | 'Closing' | 'Closed'

/**
 * Options for useTaskWebSocket hook
 */
export interface UseTaskWebSocketOptions {
  /** Enable/disable WebSocket connection. Default: true */
  enabled?: boolean
  /** Optional callback when event is received */
  onEvent?: (event: TaskEvent) => void
}

/**
 * Return type for useTaskWebSocket hook
 */
export interface UseTaskWebSocketReturn {
  /** Latest WebSocket event received */
  lastEvent: TaskEvent | null
  /** Current connection status */
  connectionStatus: ConnectionStatus
  /** Convenience flag - true when connection is open */
  isConnected: boolean
  /** Connection error if any */
  error: Event | null
}

/**
 * Hook for managing WebSocket connection to /api/ws/tasks endpoint
 *
 * Features:
 * - Automatic authentication via WebSocket subprotocols (Bearer token)
 * - Exponential backoff reconnection (5s → 160s max)
 * - Connection sharing across multiple components
 * - Proper cleanup on unmount
 *
 * Authentication:
 * - Uses WebSocket subprotocols to pass JWT Bearer token
 * - Format: `["Authorization", "{token}"]`
 * - Sent in Sec-WebSocket-Protocol header during HTTP upgrade
 * - Browser WebSocket API doesn't support custom headers, subprotocols are standard alternative
 * - Backend must extract token from subprotocol during handshake
 *
 * @example
 * ```typescript
 * const { lastEvent, isConnected, connectionStatus } = useTaskWebSocket({
 *   enabled: !!session,
 *   onEvent: (event) => console.log('Task event:', event)
 * })
 * ```
 *
 * Pattern based on: frontend/src/hooks/flow/useProcessInstanceWithWS.ts
 */
export const useTaskWebSocket = (options: UseTaskWebSocketOptions = {}): UseTaskWebSocketReturn => {
  const { enabled = true, onEvent } = options
  const { session } = useSession()

  // Build WebSocket URL without authentication (auth passed via protocols)
  // Only connect if enabled and session with access token is available
  const socketUrl = useMemo(() => {
    if (!enabled || !session?.access_token) {
      return null
    }
    return `${env('NEXT_PUBLIC_WAREHOUSE_WS_API')}/tasks`
  }, [enabled, session?.access_token])

  // Build authentication subprotocol
  // Browser WebSocket API doesn't support custom headers (security restriction)
  // WebSocket subprotocols are the standard way to pass auth during handshake
  // Format per react-use-websocket docs: ["Authorization", "token"]
  const protocols = useMemo(() => {
    if (!session?.access_token) {
      return undefined
    }
    // Pass Authorization header as WebSocket subprotocol
    // Sent in Sec-WebSocket-Protocol header during HTTP upgrade
    // Format: ["Authorization", "{token}"]
    return ['Authorization', `${session.access_token}`]
  }, [session?.access_token])

  // Configure WebSocket with reconnection and sharing
  const { lastJsonMessage, readyState } = useWebSocket<TaskEvent>(socketUrl, {
    // Authentication via WebSocket subprotocol (browser-compatible alternative to headers)
    // The backend should extract the token from the Sec-WebSocket-Protocol header
    protocols,

    // Connection sharing - single connection for multiple components
    share: true,

    // Reconnection strategy
    shouldReconnect: () => true, // Always attempt reconnection
    reconnectAttempts: Infinity, // Never stop trying
    retryOnError: true,

    // Exponential backoff: 5s, 10s, 20s, 40s, 80s, then cap at 160s
    reconnectInterval: (attemptNumber: number) => {
      const baseDelay = 5000 // 5 seconds
      const maxDelay = 160000 // 160 seconds
      const delay = baseDelay * Math.pow(2, Math.min(attemptNumber, 5))
      return Math.min(delay, maxDelay)
    },

    // Event handlers for debugging (development only)
    onOpen: () => {
      if (process.env.NODE_ENV === 'development') {
        console.log('[TaskWS] Connected to', socketUrl)
      }
    },
    onClose: () => {
      if (process.env.NODE_ENV === 'development') {
        console.log('[TaskWS] Disconnected')
      }
    },
    onError: (error) => {
      if (process.env.NODE_ENV === 'development') {
        console.error('[TaskWS] Connection error:', error)
      }
    },
    onMessage: (message) => {
      if (process.env.NODE_ENV === 'development') {
        console.log('[TaskWS] Event received:', message.data)
      }
    },
  })

  // Call optional event callback when message received
  if (lastJsonMessage && onEvent) {
    onEvent(lastJsonMessage)
  }

  // Map ReadyState to ConnectionStatus
  const connectionStatus: ConnectionStatus = {
    [ReadyState.UNINSTANTIATED]: 'Uninstantiated',
    [ReadyState.CONNECTING]: 'Connecting',
    [ReadyState.OPEN]: 'Open',
    [ReadyState.CLOSING]: 'Closing',
    [ReadyState.CLOSED]: 'Closed',
  }[readyState] as ConnectionStatus

  return {
    lastEvent: lastJsonMessage,
    connectionStatus,
    isConnected: readyState === ReadyState.OPEN,
    error: null, // Error handling via onError callback
  }
}
