'use client'

import { FC, useCallback, useState } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { noop } from 'lodash'
import { toast } from 'react-toastify'

import { VariablePayload, getTaskVariables } from '@/actions/engine'
import { Caption, Card, Show } from '@/components/ui'
import Dialog from '@/components/ui/Dialog'
import IconRight from '@/images/icons/chevron-right.svg'
import { FlowClientObject } from '@/services/flow'
import { trackButtonClick } from '@/utils/analytics'

import { TaskForm } from './TaskForm'

import styles from './Task.module.scss'

type TaskProps = {
  title: string
  description?: string | null
  id: string
  taskKey?: string | null
  onComplete?: (id?: string, variables?: Record<string, VariablePayload>) => void
}

export const Task: FC<TaskProps> = ({ title, id, taskKey, onComplete, description }) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isPending, setIsPending] = useState(false)

  const queryClient = useQueryClient()

  const handleClickClose = useCallback(() => {
    trackButtonClick('Button', 'Click', 'Close task Button')
    setIsOpen(false)
  }, [])

  const handleClickOpen = useCallback(() => {
    trackButtonClick('Button', 'Click', 'Open task Button')
    setIsOpen(true)
  }, [])

  const handleComplete = useCallback(
    async (variables: Awaited<ReturnType<typeof getTaskVariables>>) => {
      setIsPending(true)

      trackButtonClick('Task', 'Complete task Button', title)

      handleClickClose()
      try {
        const formattedVariables: Record<string, VariablePayload> = Object.entries(
          variables
        ).reduce(
          (acc, [key, value]) => {
            acc[key] = {
              ...value,
              valueInfo: value.valueInfo || {}, // Ensure valueInfo is an object
            } as VariablePayload
            return acc
          },
          {} as Record<string, VariablePayload>
        )

        console.log('Sending to API from Task:', formattedVariables) // Debugging output

        await FlowClientObject.engine.task.complete(id, formattedVariables)

        toast.success('Task completed')
        onComplete?.(id, formattedVariables)
      } catch (e) {
        console.error(e)
        toast.error('Error completing task')
      } finally {
        setIsPending(false)
      }
    },
    [id, title, handleClickClose, queryClient, onComplete]
  )

  return (
    <>
      <Card
        className={clsx(styles.container, {
          [styles.active]: !isPending,
          [styles.pending]: isPending,
        })}
        onClick={!isOpen && !isPending ? handleClickOpen : noop}>
        <div className={styles.body}>
          <Caption variant="body" size="sm" strong className={styles.title}>
            {title}
          </Caption>
          <Show if={description}>
            <Caption size="xs" className={styles.subtitle}>
              {description}
            </Caption>
          </Show>
        </div>
        <div className={styles.footer}>
          <IconRight className={styles.icon} />
        </div>

        <Dialog isOpen={isOpen} className={styles.modal} onClose={handleClickClose}>
          <TaskForm title={title} id={id} taskKey={taskKey} onComplete={handleComplete} />
        </Dialog>
      </Card>
    </>
  )
}
