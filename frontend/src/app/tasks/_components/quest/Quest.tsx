'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'

import { useCallback, useState } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { toast } from 'react-toastify'

import { getProcessInstances, getTasks } from '@/actions/engine'
import { Avatar, Burns, Button, Caption, Card, Show } from '@/components/ui'
import { questCustomRoute } from '@/config/custom'
import { FlowClientObject } from '@/services/flow'
import { trackButtonClick } from '@/utils/analytics'

import { HistoryTask } from '../task/HistoryTask'
import { Task } from '../task/Task'

import styles from './Quest.module.scss'

export type QuestProps = {
  isDisabled?: boolean
  id: string
  flowKey: string
  title: string
  description?: string
  img?: string | null
  reward?: number
  className?: string
  instances?: Awaited<ReturnType<typeof getProcessInstances>>
  tasks?: Awaited<ReturnType<typeof getTasks>>
}

export function Quest({
  isDisabled,
  flowKey,
  title,
  description,
  img,
  instances,
  tasks,
  reward,
}: QuestProps) {
  const queryClient = useQueryClient()
  const [isPending, setIsPending] = useState(false)
  const router = useRouter()

  const questHref = questCustomRoute[flowKey]

  const startQuestHandler = useCallback(async () => {
    trackButtonClick('Quest', instances ? 'Stop' : 'Start', title)
    setIsPending(true)
    if (questCustomRoute[flowKey]) {
      router.push(questCustomRoute[flowKey])
      return
    }

    try {
      await FlowClientObject.engine.process.definitions.start(flowKey, {})
    } catch (error) {
      console.error('Error starting quest:', error)
      toast.error('Error starting quest')
      setIsPending(false)
    }

    queryClient.invalidateQueries({
      queryKey: ['FlowClientObject.engine.process.instance.list'],
    })
  }, [flowKey, instances, title, queryClient, router])

  const questContent = (
    <>
      {!!img && <Avatar src={img} alt={title} className={styles.illustration} />}
      <div className={styles.title}>
        <Caption size="lg" strong className={styles.title}>
          {title}
        </Caption>
        <Caption size="xs" className={styles.subtitle}>
          {description}{' '}
          <Show if={reward}>
            <Burns size="xs" strong>
              +{reward}
            </Burns>
          </Show>
        </Caption>
      </div>
      <Show if={!questCustomRoute[flowKey] && !instances?.length}>
        <Button
          variant="primary"
          className={styles.action}
          size="sm"
          disabled={isDisabled || !!instances?.length}
          isPending={isPending}
          onClick={startQuestHandler}>
          {instances?.length === 0 ? 'Start' : 'Stop'}
        </Button>
      </Show>
    </>
  )

  const questClassName = clsx(styles.header, {
    [styles.active]: !isDisabled && instances?.length,
    [styles.custom]: questHref,
    [styles.hasTasks]: tasks?.length,
  })

  const handleComplete = () => {
    queryClient.invalidateQueries({
      queryKey: ['FlowClientObject.engine.task.list'],
    })
    queryClient.invalidateQueries({
      queryKey: ['FlowClientObject.engine.process.instance.list'],
    })
  }

  return (
    <div className={styles.container}>
      <Show if={questHref}>
        <Link href={questHref} className={questClassName}>
          {questContent}
        </Link>
      </Show>
      <Show if={!questHref}>
        <Card className={questClassName}>{questContent}</Card>
      </Show>

      {tasks?.map((task) => {
        if (task.state === 'COMPLETED') {
          return <HistoryTask key={task.id} title={task.name} description={task.description} />
        }

        if (task.state === 'ACTIVE') {
          return (
            <Task
              title={task.name}
              icon={img}
              description={task.description}
              key={task.id}
              taskKey={task.taskDefinitionKey}
              flowKey={flowKey}
              id={task.id}
              onComplete={handleComplete}
            />
          )
        }

        return null
      })}
    </div>
  )
}
