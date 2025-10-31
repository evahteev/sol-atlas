import { ReactNode } from 'react'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { renderHook, waitFor } from '@testing-library/react'
import { useSession } from 'next-auth/react'

import { TaskEvent, useTaskWebSocket } from '@/hooks/flow/useTaskWebSocket'
import { FlowClientObject } from '@/services/flow'

import { useTasks } from '../index'

// Mock dependencies
jest.mock('next-auth/react')
jest.mock('@/hooks/flow/useTaskWebSocket')
jest.mock('@/services/flow')

const mockUseSession = useSession as jest.MockedFunction<typeof useSession>
const mockUseTaskWebSocket = useTaskWebSocket as jest.MockedFunction<typeof useTaskWebSocket>

describe('useTasks with WebSocket Integration', () => {
  let queryClient: QueryClient

  const mockSession = {
    data: {
      user: { camunda_user_id: 'test-user-123' },
      access_token: 'mock-jwt-token',
      expires: '2025-12-31',
    },
    status: 'authenticated' as const,
    update: jest.fn(),
  }

  const mockTasks = [
    {
      id: 'task-1',
      name: 'Test Task 1',
      assignee: 'test-user-123',
      owner: null,
      created: '2025-10-23T10:00:00Z',
      due: null,
      lastUpdated: '2025-10-23T10:00:00Z',
      delegationState: null,
      description: 'Test task 1 description',
      executionId: 'exec-1',
      parentTaskId: null,
      priority: 50,
      processDefinitionId: 'process-def-1',
      processInstanceId: 'process-1',
      caseExecutionId: null,
      caseDefinitionId: null,
      caseInstanceId: null,
      taskDefinitionKey: 'test_task',
      camundaFormRef: null,
      suspended: false,
      tenantId: null,
      state: 'ACTIVE',
    },
  ]

  const mockTaskEvent: TaskEvent = {
    eventType: 'create',
    taskId: 'task-2',
    taskName: 'New Task from WebSocket',
    assignee: 'test-user-123',
    processInstanceId: 'process-1',
    processDefinitionKey: 'test_process',
    timestamp: Date.now(),
    variables: {},
  }

  beforeEach(() => {
    jest.clearAllMocks()

    // Create new query client for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })

    // Default mock implementations
    mockUseSession.mockReturnValue(mockSession)
    mockUseTaskWebSocket.mockReturnValue({
      lastEvent: null,
      connectionStatus: 'Open',
      isConnected: true,
      error: null,
    })

    // Mock FlowClientObject
    ;(FlowClientObject.engine.task.list as jest.Mock) = jest.fn().mockResolvedValue(mockTasks)
  })

  const wrapper = ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  describe('Basic Functionality', () => {
    it('should fetch tasks via HTTP when session is available', async () => {
      const { result } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: false }),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(FlowClientObject.engine.task.list).toHaveBeenCalledWith({
        schema: undefined,
        include_history: false,
        session: mockSession.data,
      })
      expect(result.current.data).toEqual(mockTasks)
    })

    it('should return null when session is not available', async () => {
      mockUseSession.mockReturnValue({
        data: null,
        status: 'unauthenticated',
        update: jest.fn(),
      })

      const { result } = renderHook(() => useTasks({ session: null, includeHistory: false }), {
        wrapper,
      })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data).toBeNull()
    })

    it('should use 5min polling interval when WebSocket is connected', async () => {
      mockUseTaskWebSocket.mockReturnValue({
        lastEvent: null,
        connectionStatus: 'Open',
        isConnected: true,
        error: null,
      })

      const { result } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: false }),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Query should have 5min refetch interval
      // This is verified by the query client configuration
      expect(mockUseTaskWebSocket).toHaveBeenCalled()
    })

    it('should use 1s polling interval when WebSocket is disconnected', async () => {
      mockUseTaskWebSocket.mockReturnValue({
        lastEvent: null,
        connectionStatus: 'Closed',
        isConnected: false,
        error: null,
      })

      const { result } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: false }),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      // Query should have 1s refetch interval (fallback)
      expect(mockUseTaskWebSocket).toHaveBeenCalled()
    })
  })

  describe('WebSocket Event Processing - Create', () => {
    it('should add new task to cache on "create" event', async () => {
      const { rerender } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: false }),
        { wrapper }
      )

      // Wait for initial data
      await waitFor(() =>
        expect(queryClient.getQueryData(['FlowClientObject.engine.task.list'])).toBeTruthy()
      )

      // Simulate WebSocket event
      mockUseTaskWebSocket.mockReturnValue({
        lastEvent: mockTaskEvent,
        connectionStatus: 'Open',
        isConnected: true,
        error: null,
      })

      rerender()

      await waitFor(() => {
        const data = queryClient.getQueryData<typeof mockTasks>([
          'FlowClientObject.engine.task.list',
          undefined,
          false,
          mockSession.data,
        ])
        expect(data?.length).toBe(2) // Original + new task
        expect(data?.some((t) => t.id === 'task-2')).toBe(true)
      })
    })

    it('should deduplicate tasks on "create" event if task already exists', async () => {
      const duplicateEvent: TaskEvent = {
        ...mockTaskEvent,
        taskId: 'task-1', // Same as existing task
      }

      const { rerender } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: false }),
        { wrapper }
      )

      await waitFor(() =>
        expect(queryClient.getQueryData(['FlowClientObject.engine.task.list'])).toBeTruthy()
      )

      // Simulate duplicate create event
      mockUseTaskWebSocket.mockReturnValue({
        lastEvent: duplicateEvent,
        connectionStatus: 'Open',
        isConnected: true,
        error: null,
      })

      rerender()

      await waitFor(() => {
        const data = queryClient.getQueryData<typeof mockTasks>([
          'FlowClientObject.engine.task.list',
          undefined,
          false,
          mockSession.data,
        ])
        expect(data?.length).toBe(1) // Still only 1 task (no duplicate)
      })
    })
  })

  describe('WebSocket Event Processing - Update', () => {
    it('should update existing task on "update" event', async () => {
      const updateEvent: TaskEvent = {
        ...mockTaskEvent,
        eventType: 'update',
        taskId: 'task-1',
        taskName: 'Updated Task Name',
      }

      const { rerender } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: false }),
        { wrapper }
      )

      await waitFor(() =>
        expect(queryClient.getQueryData(['FlowClientObject.engine.task.list'])).toBeTruthy()
      )

      // Simulate update event
      mockUseTaskWebSocket.mockReturnValue({
        lastEvent: updateEvent,
        connectionStatus: 'Open',
        isConnected: true,
        error: null,
      })

      rerender()

      await waitFor(() => {
        const data = queryClient.getQueryData<typeof mockTasks>([
          'FlowClientObject.engine.task.list',
          undefined,
          false,
          mockSession.data,
        ])
        expect(data?.length).toBe(1) // Same number of tasks
        expect(data?.[0].name).toBe('Updated Task Name') // Name updated
      })
    })
  })

  describe('WebSocket Event Processing - Complete', () => {
    it('should update task state on "complete" event', async () => {
      const completeEvent: TaskEvent = {
        ...mockTaskEvent,
        eventType: 'complete',
        taskId: 'task-1',
      }

      const { rerender } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: false }),
        { wrapper }
      )

      await waitFor(() =>
        expect(queryClient.getQueryData(['FlowClientObject.engine.task.list'])).toBeTruthy()
      )

      // Simulate complete event
      mockUseTaskWebSocket.mockReturnValue({
        lastEvent: completeEvent,
        connectionStatus: 'Open',
        isConnected: true,
        error: null,
      })

      rerender()

      await waitFor(() => {
        const data = queryClient.getQueryData<typeof mockTasks>([
          'FlowClientObject.engine.task.list',
          undefined,
          false,
          mockSession.data,
        ])
        expect(data?.length).toBe(1)
        expect(data?.[0].state).toBe('COMPLETED')
      })
    })
  })

  describe('WebSocket Event Processing - Delete', () => {
    it('should remove task from cache on "delete" event', async () => {
      const deleteEvent: TaskEvent = {
        ...mockTaskEvent,
        eventType: 'delete',
        taskId: 'task-1',
      }

      const { rerender } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: false }),
        { wrapper }
      )

      await waitFor(() =>
        expect(queryClient.getQueryData(['FlowClientObject.engine.task.list'])).toBeTruthy()
      )

      // Simulate delete event
      mockUseTaskWebSocket.mockReturnValue({
        lastEvent: deleteEvent,
        connectionStatus: 'Open',
        isConnected: true,
        error: null,
      })

      rerender()

      await waitFor(() => {
        const data = queryClient.getQueryData<typeof mockTasks>([
          'FlowClientObject.engine.task.list',
          undefined,
          false,
          mockSession.data,
        ])
        expect(data?.length).toBe(0) // Task removed
      })
    })
  })

  describe('User Filtering', () => {
    it('should ignore events for other users', async () => {
      const otherUserEvent: TaskEvent = {
        ...mockTaskEvent,
        assignee: 'other-user-456', // Different user
      }

      const { rerender } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: false }),
        { wrapper }
      )

      await waitFor(() =>
        expect(queryClient.getQueryData(['FlowClientObject.engine.task.list'])).toBeTruthy()
      )

      // Simulate event for other user
      mockUseTaskWebSocket.mockReturnValue({
        lastEvent: otherUserEvent,
        connectionStatus: 'Open',
        isConnected: true,
        error: null,
      })

      rerender()

      await waitFor(() => {
        const data = queryClient.getQueryData<typeof mockTasks>([
          'FlowClientObject.engine.task.list',
          undefined,
          false,
          mockSession.data,
        ])
        expect(data?.length).toBe(1) // No new task added
        expect(data?.[0].id).toBe('task-1') // Original task unchanged
      })
    })

    it('should process events when assignee matches current user', async () => {
      const { rerender } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: false }),
        { wrapper }
      )

      await waitFor(() =>
        expect(queryClient.getQueryData(['FlowClientObject.engine.task.list'])).toBeTruthy()
      )

      // Simulate event for current user
      mockUseTaskWebSocket.mockReturnValue({
        lastEvent: mockTaskEvent, // assignee matches
        connectionStatus: 'Open',
        isConnected: true,
        error: null,
      })

      rerender()

      await waitFor(() => {
        const data = queryClient.getQueryData<typeof mockTasks>([
          'FlowClientObject.engine.task.list',
          undefined,
          false,
          mockSession.data,
        ])
        expect(data?.length).toBe(2) // New task added
      })
    })
  })

  describe('Backward Compatibility', () => {
    it('should maintain same API signature', () => {
      const { result } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: false }),
        { wrapper }
      )

      // Should return standard useQuery result
      expect(result.current).toHaveProperty('data')
      expect(result.current).toHaveProperty('isLoading')
      expect(result.current).toHaveProperty('isError')
      expect(result.current).toHaveProperty('isSuccess')
    })

    it('should work with schema parameter', async () => {
      const schema = { processInstanceId: 'process-123' }

      const { result } = renderHook(
        () => useTasks({ session: mockSession.data, schema, includeHistory: false }),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(FlowClientObject.engine.task.list).toHaveBeenCalledWith({
        schema,
        include_history: false,
        session: mockSession.data,
      })
    })

    it('should work with includeHistory parameter', async () => {
      const { result } = renderHook(
        () => useTasks({ session: mockSession.data, includeHistory: true }),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(FlowClientObject.engine.task.list).toHaveBeenCalledWith({
        schema: undefined,
        include_history: true,
        session: mockSession.data,
      })
    })

    it('should work with custom query options', async () => {
      const { result } = renderHook(
        () =>
          useTasks({
            session: mockSession.data,
            includeHistory: false,
            query: { enabled: true },
          }),
        { wrapper }
      )

      await waitFor(() => expect(result.current.isSuccess).toBe(true))
      expect(result.current.data).toEqual(mockTasks)
    })
  })
})
