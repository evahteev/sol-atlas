import { ReactNode } from 'react'

import { Session } from '@/lib/session'

export type TaskFormVariable = {
  value: unknown
  type?: string | null
  label?: string | null
  valueInfo?: Record<string, never> | null
}

export type TaskFormProps = {
  title?: ReactNode
  description?: string | null
  className?: string
  icon?: string | null
  definitionKey: string
  instanceId?: string
  taskId?: string
  variables?: Record<string, TaskFormVariable>
  startVariables?: Record<string, TaskFormVariable>
  isLoading?: boolean
  isError?: boolean
  session?: Session | null
  onComplete?: (params?: {
    business_key?: string
    variables: Record<string, TaskFormVariable>
  }) => void
} & (
  | { taskId: string; startForm?: never }
  | { startForm: string | 'embedded' | 'none' | 'unknown' }
)
