'use client'

import { FC } from 'react'

import StateMessage from '@/components/composed/StateMessage'
import { useStartFormVariables, useTaskFormVariables } from '@/services/flow/hooks/engine'
import { components } from '@/services/flow/schema'

import { taskCustomComponent } from '../custom'
import { TaskFormProps } from '../types'
import { TaskFormFromVarsForm } from './TaskFormFromVarsForm'

export const TaskFormFromVars: FC<
  TaskFormProps & { task?: components['schemas']['TaskSchema'] }
> = ({ onComplete, task, ...props }) => {
  const { definitionKey, startForm, startVariables } = props

  const isVariableStartForm = startForm === 'embedded'

  const { data: variablesStartForm, isLoading: isLoadingStartFormVars } = useStartFormVariables(
    definitionKey,
    {
      // placeholderData: undefined,
      enabled: isVariableStartForm,

      refetchInterval: false,
      refetchOnWindowFocus: false,
      refetchIntervalInBackground: false,
      refetchOnMount: false,
    }
  )

  const {
    data: variablesTaskForm,
    isLoading: isLoadingTaskFormVars,
    isError,
  } = useTaskFormVariables(task?.id ?? '', {
    // placeholderData: undefined,
    enabled: !!task,

    refetchInterval: false,
    refetchOnWindowFocus: false,
    refetchIntervalInBackground: false,
    refetchOnMount: false,
  })

  const isLoading = isLoadingStartFormVars || isLoadingTaskFormVars

  if (!isVariableStartForm && !task && !props.isLoading) {
    return <StateMessage type="danger" caption="This task cannot be rendered" />
  }

  const variables = isVariableStartForm
    ? { ...variablesStartForm, ...startVariables } // override bpmn start vars with the start vars from props
    : variablesTaskForm

  const CustomForm =
    (isVariableStartForm
      ? taskCustomComponent?.[definitionKey ?? '']?.start
      : taskCustomComponent?.[definitionKey ?? '']?.tasks?.[task?.taskDefinitionKey ?? '']) ?? null

  if (CustomForm) {
    return (
      <CustomForm
        {...props}
        isStartForm={isVariableStartForm}
        variables={variables}
        isLoading={isLoading}
        isError={isError}
        onComplete={onComplete}
      />
    )
  }

  return (
    <TaskFormFromVarsForm
      {...props}
      title={task?.name ?? props.title}
      description={task?.description ?? props.description}
      definitionKey={task?.taskDefinitionKey ?? ''}
      instanceId={task?.processInstanceId}
      variables={variables}
      isLoading={isLoading}
      isError={isError}
      onComplete={onComplete}
    />
  )
}
