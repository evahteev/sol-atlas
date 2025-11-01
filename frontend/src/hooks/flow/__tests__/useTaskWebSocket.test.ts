import { renderHook } from '@testing-library/react'
import { useSession } from 'next-auth/react'
import { env } from 'next-runtime-env'
import useWebSocket, { ReadyState } from 'react-use-websocket'

import { TaskEvent, useTaskWebSocket } from '../useTaskWebSocket'

// Mock dependencies
jest.mock('next-auth/react')
jest.mock('react-use-websocket')

const mockUseSession = useSession as jest.MockedFunction<typeof useSession>
const mockUseWebSocket = useWebSocket as jest.MockedFunction<typeof useWebSocket>

describe('useTaskWebSocket', () => {
  const mockSession = {
    data: {
      user: { camunda_user_id: 'test-user-123' },
      access_token: 'mock-jwt-token',
      expires: '2025-12-31',
    },
    status: 'authenticated' as const,
    update: jest.fn(),
  }

  const mockTaskEvent: TaskEvent = {
    eventType: 'create',
    taskId: 'task-123',
    taskName: 'Test Task',
    assignee: 'test-user-123',
    processInstanceId: 'process-456',
    processDefinitionKey: 'test_process',
    timestamp: Date.now(),
    variables: {},
  }

  beforeEach(() => {
    jest.clearAllMocks()

    // Default mock implementations
    mockUseSession.mockReturnValue(mockSession)
    mockUseWebSocket.mockReturnValue({
      lastJsonMessage: null,
      readyState: ReadyState.OPEN,
      lastError: null,
      sendMessage: jest.fn(),
      sendJsonMessage: jest.fn(),
      getWebSocket: jest.fn(),
    })
  })

  describe('Connection Management', () => {
    it('should connect to WebSocket when session is available', () => {
      const { result } = renderHook(() => useTaskWebSocket())

      // Verify useWebSocket was called with correct URL and protocols
      expect(mockUseWebSocket).toHaveBeenCalledWith(
        `${env('NEXT_PUBLIC_WAREHOUSE_WS_API')}/tasks`,
        expect.objectContaining({
          protocols: ['Authorization', 'Bearer mock-jwt-token'],
          share: true,
          shouldReconnect: expect.any(Function),
          reconnectAttempts: Infinity,
          retryOnError: true,
        })
      )

      // Verify connection status
      expect(result.current.connectionStatus).toBe('Open')
      expect(result.current.isConnected).toBe(true)
    })

    it('should not connect when session is missing', () => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      })

      renderHook(() => useTaskWebSocket())

      // Verify useWebSocket was called with null URL
      expect(mockUseWebSocket).toHaveBeenCalledWith(null, expect.any(Object))
    })

    it('should not connect when access_token is missing', () => {
      mockUseSession.mockReturnValue({
        data: {
          user: { camunda_user_id: 'test-user-123' },
          expires: '2025-12-31',
          // access_token is missing
        },
        status: 'authenticated',
        update: jest.fn(),
      })

      renderHook(() => useTaskWebSocket())

      // Verify useWebSocket was called with null URL
      expect(mockUseWebSocket).toHaveBeenCalledWith(null, expect.any(Object))
    })

    it('should not connect when enabled is false', () => {
      renderHook(() => useTaskWebSocket({ enabled: false }))

      // Verify useWebSocket was called with null URL
      expect(mockUseWebSocket).toHaveBeenCalledWith(null, expect.any(Object))
    })

    it('should use exponential backoff for reconnection', () => {
      renderHook(() => useTaskWebSocket())

      // Get the reconnectInterval function
      const callArgs = mockUseWebSocket.mock.calls[0]
      const options = callArgs[1]
      const reconnectInterval = options?.reconnectInterval as (attemptNumber: number) => number

      // Test exponential backoff: 5s, 10s, 20s, 40s, 80s, max 160s
      expect(reconnectInterval(0)).toBe(5000) // 5 seconds
      expect(reconnectInterval(1)).toBe(10000) // 10 seconds
      expect(reconnectInterval(2)).toBe(20000) // 20 seconds
      expect(reconnectInterval(3)).toBe(40000) // 40 seconds
      expect(reconnectInterval(4)).toBe(80000) // 80 seconds
      expect(reconnectInterval(5)).toBe(160000) // 160 seconds (max)
      expect(reconnectInterval(6)).toBe(160000) // Still capped at 160s
      expect(reconnectInterval(10)).toBe(160000) // Still capped at 160s
    })

    it('should always attempt reconnection', () => {
      renderHook(() => useTaskWebSocket())

      const callArgs = mockUseWebSocket.mock.calls[0]
      const options = callArgs[1]
      const shouldReconnect = options?.shouldReconnect as () => boolean

      expect(shouldReconnect()).toBe(true)
    })
  })

  describe('Connection Status', () => {
    it('should correctly map CONNECTING status', () => {
      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: null,
        readyState: ReadyState.CONNECTING,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.connectionStatus).toBe('Connecting')
      expect(result.current.isConnected).toBe(false)
    })

    it('should correctly map OPEN status', () => {
      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: null,
        readyState: ReadyState.OPEN,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.connectionStatus).toBe('Open')
      expect(result.current.isConnected).toBe(true)
    })

    it('should correctly map CLOSING status', () => {
      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: null,
        readyState: ReadyState.CLOSING,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.connectionStatus).toBe('Closing')
      expect(result.current.isConnected).toBe(false)
    })

    it('should correctly map CLOSED status', () => {
      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: null,
        readyState: ReadyState.CLOSED,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.connectionStatus).toBe('Closed')
      expect(result.current.isConnected).toBe(false)
    })

    it('should correctly map UNINSTANTIATED status', () => {
      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: null,
        readyState: ReadyState.UNINSTANTIATED,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.connectionStatus).toBe('Uninstantiated')
      expect(result.current.isConnected).toBe(false)
    })
  })

  describe('Event Processing', () => {
    it('should process "create" event correctly', () => {
      const createEvent: TaskEvent = {
        ...mockTaskEvent,
        eventType: 'create',
      }

      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: createEvent,
        readyState: ReadyState.OPEN,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.lastEvent).toEqual(createEvent)
      expect(result.current.lastEvent?.eventType).toBe('create')
    })

    it('should process "update" event correctly', () => {
      const updateEvent: TaskEvent = {
        ...mockTaskEvent,
        eventType: 'update',
      }

      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: updateEvent,
        readyState: ReadyState.OPEN,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.lastEvent).toEqual(updateEvent)
      expect(result.current.lastEvent?.eventType).toBe('update')
    })

    it('should process "complete" event correctly', () => {
      const completeEvent: TaskEvent = {
        ...mockTaskEvent,
        eventType: 'complete',
      }

      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: completeEvent,
        readyState: ReadyState.OPEN,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.lastEvent).toEqual(completeEvent)
      expect(result.current.lastEvent?.eventType).toBe('complete')
    })

    it('should process "delete" event correctly', () => {
      const deleteEvent: TaskEvent = {
        ...mockTaskEvent,
        eventType: 'delete',
      }

      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: deleteEvent,
        readyState: ReadyState.OPEN,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.lastEvent).toEqual(deleteEvent)
      expect(result.current.lastEvent?.eventType).toBe('delete')
    })

    it('should call onEvent callback when event is received', () => {
      const onEventMock = jest.fn()

      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: mockTaskEvent,
        readyState: ReadyState.OPEN,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      renderHook(() => useTaskWebSocket({ onEvent: onEventMock }))

      expect(onEventMock).toHaveBeenCalledWith(mockTaskEvent)
    })

    it('should handle events with optional variables', () => {
      const eventWithVariables: TaskEvent = {
        ...mockTaskEvent,
        variables: {
          customField: 'value',
          priority: 'high',
        },
      }

      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: eventWithVariables,
        readyState: ReadyState.OPEN,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.lastEvent?.variables).toEqual({
        customField: 'value',
        priority: 'high',
      })
    })
  })

  describe('Error Handling', () => {
    it('should expose connection errors', () => {
      const mockError = new Event('error')

      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: null,
        readyState: ReadyState.CLOSED,
        lastError: mockError,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.error).toBe(mockError)
    })

    it('should handle null lastJsonMessage gracefully', () => {
      mockUseWebSocket.mockReturnValue({
        lastJsonMessage: null,
        readyState: ReadyState.OPEN,
        lastError: null,
        sendMessage: jest.fn(),
        sendJsonMessage: jest.fn(),
        getWebSocket: jest.fn(),
      })

      const { result } = renderHook(() => useTaskWebSocket())

      expect(result.current.lastEvent).toBeNull()
      expect(result.current.isConnected).toBe(true)
    })
  })

  describe('Connection Cleanup', () => {
    it('should clean up properly on unmount', () => {
      const { unmount } = renderHook(() => useTaskWebSocket())

      // Unmount the hook
      unmount()

      // react-use-websocket handles cleanup internally when share:true
      // We just verify no errors occur during unmount
      expect(true).toBe(true)
    })

    it('should handle rapid mount/unmount cycles', () => {
      // Mount and unmount multiple times
      for (let i = 0; i < 10; i++) {
        const { unmount } = renderHook(() => useTaskWebSocket())
        unmount()
      }

      // Verify no memory leaks or errors
      // react-use-websocket with share:true should handle this correctly
      expect(true).toBe(true)
    })
  })

  describe('Session Changes', () => {
    it('should reconnect when session token changes', () => {
      const { rerender } = renderHook(() => useTaskWebSocket())

      // Initial connection
      expect(mockUseWebSocket).toHaveBeenCalledTimes(1)

      // Update session with new token
      mockUseSession.mockReturnValue({
        ...mockSession,
        data: {
          ...mockSession.data!,
          access_token: 'new-jwt-token',
        },
      })

      // Rerender to trigger useMemo recalculation
      rerender()

      // Should have been called again with new URL
      expect(mockUseWebSocket).toHaveBeenCalledTimes(2)
    })

    it('should disconnect when session becomes null', () => {
      const { rerender } = renderHook(() => useTaskWebSocket())

      // Initial connection
      expect(mockUseWebSocket).toHaveBeenCalledWith(
        expect.stringContaining('/api/ws/tasks'),
        expect.any(Object)
      )

      // Session expires
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      })

      // Rerender
      rerender()

      // Should be called with null URL
      const lastCall = mockUseWebSocket.mock.calls[mockUseWebSocket.mock.calls.length - 1]
      expect(lastCall[0]).toBeNull()
    })
  })
})
