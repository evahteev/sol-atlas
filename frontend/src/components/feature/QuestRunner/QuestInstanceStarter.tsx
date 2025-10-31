'use client'

import { FC, ReactNode, useEffect, useState } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { Session } from 'next-auth'

import Loader from '@/components/atoms/Loader'
import RequireLogin from '@/components/composed/RequireLogin'
import StateMessage from '@/components/composed/StateMessage'
import TaskForm from '@/components/composed/TaskForm'
import { TaskFormVariable } from '@/components/composed/TaskForm/types'
import Card from '@/components/ui/Card'
import { useDidMount } from '@/hooks/useDidMount'
import { FlowClientObject } from '@/services/flow'
import { useFlows } from '@/services/flow/hooks/flow'
import { components } from '@/services/flow/schema'

import styles from './QuestRunner.module.scss'

export type QuestInstanceStarterProps = {
  processDefinitionKey: string
  startVariables?: {
    [key: string]: components['schemas']['VariableValueSchema']
  }
  onInstanceStart?: (instance: components['schemas']['ProcessInstanceSchema']) => void
  session?: Session | null
  loader?: ReactNode
  className?: string
}

export const QuestInstanceStarter: FC<QuestInstanceStarterProps> = ({
  processDefinitionKey,
  startVariables,
  onInstanceStart,
  session,
  loader,
  className,
}) => {
  const queryClient = useQueryClient()
  const isMounted = useDidMount()
  const { data: flows, isLoading } = useFlows()
  const definition = flows?.find((flow) => flow.key === processDefinitionKey)
  const [isRequiredLogin, setIsRequredLogin] = useState(false)

  const isStartForm = definition?.start_form !== 'none'

  const handleStart = (params?: {
    business_key?: string
    variables?: Record<string, TaskFormVariable>
  }) => {
    if (!session) {
      setIsRequredLogin(true)
      return
    }

    const startParams: {
      business_key?: string
      variables?: Record<string, TaskFormVariable>
    } = params ?? {}
    startParams.variables = { ...startVariables, ...(startParams?.variables ?? {}) }
    FlowClientObject.engine.process.definitions
      .start(processDefinitionKey, startParams, session)
      .then((instance) => {
        queryClient.invalidateQueries({
          queryKey: ['FlowClientObject.engine.process.instance.list'],
        })
        onInstanceStart?.(instance)
      })
  }

  useEffect(() => {
    const isAllowed = !!definition && !isStartForm

    if (!isAllowed || !session || !isMounted) {
      return
    }

    console.info(`Starting ${processDefinitionKey}`)

    handleStart()
  })

  if (!isLoading && definition?.key !== processDefinitionKey) {
    return <StateMessage type="danger" caption="Can't find process definition" />
  }

  if (!isLoading) {
    return (
      <RequireLogin isRequired={isRequiredLogin}>
        <Card className={clsx(styles.container, className)}>
          <TaskForm
            className={styles.task}
            startForm={definition?.start_form || 'none'}
            startVariables={startVariables}
            title={definition?.name ?? undefined}
            description={definition?.description ?? undefined}
            definitionKey={processDefinitionKey}
            onComplete={handleStart}
            session={session}
          />
        </Card>
      </RequireLogin>
    )
  }

  return loader ?? <Loader className={styles.loader}>Starting process...</Loader>
}
