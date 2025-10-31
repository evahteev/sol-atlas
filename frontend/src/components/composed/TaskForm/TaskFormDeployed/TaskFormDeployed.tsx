'use client'

import Image from 'next/image'

import { FC, FormEventHandler, SyntheticEvent, useState } from 'react'

import clsx from 'clsx'
import DOMPurify from 'isomorphic-dompurify'
import { noop } from 'lodash'
import { marked } from 'marked'
import { toast } from 'react-toastify'

import Loader from '@/components/atoms/Loader'
import StateMessage from '@/components/composed/StateMessage'
import { getTaskFormDataToObject, getVariablesFromObject } from '@/components/composed/TaskForm'
import Button, { ButtonProps } from '@/components/ui/Button'
import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
import { useDeployedStartForm, useTaskDeployedForm } from '@/services/flow/hooks/engine'

import { TaskFormProps } from '../types'
import { TaskFormDeployedLayout } from './TaskFormDeployedLayout'
import { TaskFormDeployedComponent } from './types'

import styles from '../TaskForm.module.scss'

const findSubmitButtonComponent = (components?: TaskFormDeployedComponent[]): boolean => {
  return !!components?.filter((component) => {
    const possibleGroup = component as { components?: TaskFormDeployedComponent[] }
    if (possibleGroup.components) {
      return findSubmitButtonComponent(possibleGroup.components)
    }

    // Check Camunda button components
    if (component.type === 'button') {
      return (
        component.action === 'submit' ||
        (component as { properties?: Record<string, string> }).properties?.type === 'submit'
      )
    }

    // Check HTML components for submit buttons
    if (component.type === 'html') {
      const htmlContent = (component as { content?: string }).content || ''
      // Detect <button type="submit"> in HTML (handles both single/double quotes)
      return /<button[^>]+type=["']submit["'][^>]*>/i.test(htmlContent)
    }

    return false
  })?.length
}

export const TaskFormDeployed: FC<TaskFormProps & { isStartForm?: boolean }> = ({
  title,
  description,
  taskId,
  instanceId,
  icon,
  className,
  isStartForm,
  definitionKey,
  onComplete,
  session,
}) => {
  const {
    data: dataTaskForm,
    isLoading: isLoadingTaskForm,
    isError: isErrorTaskForm,
  } = useTaskDeployedForm({
    taskId: taskId ?? '',
    instanceId: instanceId ?? '',
    query: {
      // placeholderData: undefined,
      enabled: !!taskId && !isStartForm,

      refetchInterval: false,
      refetchOnWindowFocus: false,
      refetchIntervalInBackground: false,
      refetchOnMount: false,
    },
  })

  const {
    data: dataStartForm,
    isLoading: isLoadingStartForm,
    isError: isErrorStartForm,
  } = useDeployedStartForm({
    definitionKey,
    query: {
      // placeholderData: undefined,
      enabled: isStartForm,

      refetchInterval: false,
      refetchOnWindowFocus: false,
      refetchIntervalInBackground: false,
      refetchOnMount: false,
    },
  })

  const data = isStartForm ? dataStartForm : dataTaskForm
  const isLoading = isLoadingStartForm || isLoadingTaskForm
  const isError = (isStartForm && isErrorStartForm) || (!!taskId && !isStartForm && isErrorTaskForm)

  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit: FormEventHandler<HTMLFormElement> = async (
    e: SyntheticEvent<HTMLFormElement, SubmitEvent>
  ) => {
    e.preventDefault()
    setIsSubmitting(true)

    const submitter = e.nativeEvent.submitter as HTMLButtonElement

    const extra: Record<string, string | number | boolean | null> = {}

    if (submitter?.tagName === 'BUTTON' && submitter?.type === 'submit') {
      extra[submitter.name] = submitter.value
    }

    const newVariables = getVariablesFromObject(getTaskFormDataToObject(e.currentTarget, extra))

    try {
      onComplete?.({
        variables: newVariables,
      })
    } catch (error) {
      console.error('Error submitting form:', error)
      toast.error('Error submitting form')
    } finally {
      setIsSubmitting(false)
      console.log('Completed task')
    }
  }

  const parsedMarkup = DOMPurify.sanitize(
    marked.parse(description ?? '', {
      async: false,
    }) as string
  )

  const hasSubmit = findSubmitButtonComponent(data?.form?.components as TaskFormDeployedComponent[])

  const propsSubmit: ButtonProps = {
    type: 'submit',
    variant: 'primary',
    size: 'xl',
    className: styles.submit,
    disabled: isSubmitting,
    isBlock: true,
  }

  return (
    <form
      className={clsx(styles.container, className)}
      onSubmit={!isLoading && !isSubmitting ? handleSubmit : noop}>
      <Show if={(title || icon || description) && isLoading}>
        <div className={styles.header}>
          <Show if={icon}>
            <Image
              src={icon ?? ''}
              alt={description ?? ''}
              width={96}
              height={96}
              className={styles.icon}
            />
          </Show>

          <Caption variant="header" size="lg" className={styles.title}>
            {title}
          </Caption>

          <Show if={description}>
            <div className={styles.subtitle} dangerouslySetInnerHTML={{ __html: parsedMarkup }} />
          </Show>
        </div>
      </Show>

      <fieldset className={styles.body} disabled={isSubmitting}>
        <Show if={isLoading}>
          <Loader className={styles.loader} />
        </Show>
        <Show if={isError}>
          <StateMessage
            type="danger"
            className={styles.message}
            caption="Error while fetching task data"
          />
        </Show>
        <Show if={!isLoading && !isError && data?.form?.components?.length}>
          <TaskFormDeployedLayout
            components={(data?.form?.components ?? []) as TaskFormDeployedComponent[]}
            variables={data?.variables}
            session={session}
            onFormComplete={onComplete}
          />
        </Show>
      </fieldset>

      <Show if={!isLoading && !hasSubmit}>
        <div className={styles.footer}>
          <Show if={isStartForm}>
            <Button {...propsSubmit} caption={session ? 'Start' : 'Login to continue'} />
          </Show>

          <Show if={!isStartForm}>
            <Button {...propsSubmit} caption="Complete task" />
          </Show>
        </div>
      </Show>
    </form>
  )
}
