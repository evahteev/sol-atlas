'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'

import { ReactNode, useCallback, useState, useTransition } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { useSession } from 'next-auth/react'
import { useTranslations } from 'next-intl'
import { toast } from 'react-toastify'

import Value from '@/components/atoms/Value'
import { questCustomRoute } from '@/components/composed/TaskForm/custom'
import Avatar from '@/components/ui/Avatar'
import Button, { ButtonProps } from '@/components/ui/Button'
import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'
import Dialog from '@/components/ui/Dialog'
import Show from '@/components/ui/Show'
import TimerCountdown from '@/components/ui/TimerCountdown'
import { useDidMount } from '@/hooks/useDidMount'
import { FlowClientObject } from '@/services/flow'
import { components } from '@/services/flow/schema'

import TaskForm from '../TaskForm'
import QuestInstance from './QuestInstance'

import styles from './Quest.module.scss'

export enum QuestTypes {
  'Regular' = 'quest',
  'Restartable' = 'quest_restart',
  'MultiInstance' = 'quest_multi-instance',
  'DAOHolder' = 'quest_daonft',
  'NoDAOHolder' = 'quest_nodaonft',
}

type QuestProps = {
  isDisabled?: boolean
  id: string
  flowKey: string
  startForm?: string | 'embedded' | 'unknown' | 'none'
  title: string
  description?: string
  img?: string | null
  reward?: number
  unit?: ReactNode
  className?: string
  instances?: Awaited<ReturnType<typeof FlowClientObject.engine.process.instance.list>>
  tasks?: Awaited<ReturnType<typeof FlowClientObject.engine.process.instance.task.list>>
  type: QuestTypes
  actions?: ButtonProps[] | ((instanceId?: string | null) => ButtonProps[] | null)
  start?: string | null
  end?: string | null
  url?: string | null
  startButtonCaption?: string | null
}

export function Quest({
  isDisabled,
  flowKey,
  startForm,
  title,
  description,
  img,
  instances,
  tasks,
  reward,
  unit,
  type,
  actions,
  start,
  end,
  url,
  startButtonCaption,
}: QuestProps) {
  const t = useTranslations('Tasks.quest')
  const queryClient = useQueryClient()
  const router = useRouter()
  const { data: session } = useSession()
  const isMounted = useDidMount()

  const [isPendingTransition, startTransition] = useTransition()

  const [isStartFormOpen, setIsStartFormOpen] = useState(false)
  const [isStartButtonLoading, setIsStartButtonLoading] = useState(false)

  const handleClickClose = useCallback(() => {
    setIsStartFormOpen(false)
  }, [])

  const handleClickOpen = useCallback(() => {
    setIsStartFormOpen(true)
  }, [])
  const questHref = questCustomRoute[flowKey]

  const startQuestHandler = useCallback(
    async (
      startParams?: components['schemas']['Body_start_process_instance_by_key_engine_process_definition_key__key__start_post']
    ) => {
      setIsStartButtonLoading(true)
      startTransition(() => {
        if (questCustomRoute[flowKey]) {
          router.push(questCustomRoute[flowKey])
          return
        }

        try {
          FlowClientObject.engine.process.definitions.start(flowKey, startParams ?? {}, session)

          if (isStartFormOpen) {
            setIsStartFormOpen(false)
          }

          queryClient.invalidateQueries({
            queryKey: ['FlowClientObject.engine.process.instance-common'],
          })
        } catch (error) {
          console.error('Error starting quest:', error)
          toast.error(t('errorStarting'))
        }
      })
      setIsStartButtonLoading(false)
    },
    [flowKey, router, session, isStartFormOpen, queryClient, t]
  )

  const restartQuestHandler = useCallback(
    async (
      startParams?: components['schemas']['Body_start_process_instance_by_key_engine_process_definition_key__key__start_post']
    ) => {
      if (!instances) {
        return
      }

      try {
        await FlowClientObject.engine.process.definitions.delete(instances[0].id)
        await startQuestHandler(startParams)
      } catch (error) {
        console.error('Error restarting quest:', error)
        toast.error(t('errorRestarting'))
      }

      queryClient.invalidateQueries({
        queryKey: ['FlowClientObject.engine.process.instance.list'],
      })
    },
    [instances, queryClient, startQuestHandler, t]
  )

  const isRegularQuestWithoutInstances = !questCustomRoute[flowKey] && !instances?.length
  // const isInstanceWithoutTasks = !!instances?.length && !tasks?.length
  const isPending = isPendingTransition

  const isStartable = !instances?.length || type === QuestTypes.MultiInstance

  const questActions = typeof actions === 'function' ? actions(instances?.[0]?.id) : actions
  const dateStart = start ? new Date((parseInt(start) || 0) * 1000) : null
  const dateEnd = end ? new Date((parseInt(end) || 0) * 1000) : null
  const currentTimestamp = Date.now()

  const isOnTimeStart = !dateStart || dateStart.getTime() <= currentTimestamp
  const isOnTimeEnd = !dateEnd || dateEnd.getTime() >= currentTimestamp
  const isOnTime = isOnTimeStart && isOnTimeEnd

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
            <Value
              suffix={<>&nbsp;{unit}</>}
              className={clsx(
                styles.reward,
                { [styles.positive]: (reward ?? 0) >= 0 },
                { [styles.negative]: (reward ?? 0) < 0 }
              )}>
              {`${reward && reward > 0 ? '+' : ''}${reward}`}
            </Value>
          </Show>
        </Caption>

        <Show if={!isOnTime}>
          <div className={styles.details}>
            <Show if={!isOnTimeStart}>
              <TimerCountdown
                timestamp={dateStart ?? 0}
                prefix={t('startingIn')}
                className={styles.timer}
              />
            </Show>
            <Show if={!isOnTimeEnd}>
              <TimerCountdown
                timestamp={dateEnd ?? 0}
                prefix={t('endedAgo')}
                suffix={t('endedAgoSuffix')}
                isCompact
                className={styles.timer}
              />
            </Show>{' '}
            <Show if={url}>
              <Link href={url || ''} target="_blank" className={styles.link}>
                {t('readMore')}
              </Link>
            </Show>
          </div>
        </Show>
      </div>
      <Show if={isOnTime}>
        <Show
          if={isMounted && (isRegularQuestWithoutInstances || type === QuestTypes.MultiInstance)}>
          <Button
            variant="primary"
            className={styles.action}
            size="sm"
            caption={isStartable ? startButtonCaption || t('start') : t('stop')}
            disabled={
              isStartButtonLoading ||
              isDisabled ||
              (!!instances?.length && type !== QuestTypes.MultiInstance)
            }
            isPending={isPending}
            onClick={() => {
              if (startForm !== 'none') {
                handleClickOpen()
              }

              if (startForm === 'none') {
                startQuestHandler()
              }
            }}
          />
        </Show>

        <Show if={!actions}>
          <Show
            if={
              isMounted &&
              !questCustomRoute[flowKey] &&
              instances?.length &&
              type === 'quest_restart'
            }>
            <Button
              variant="danger"
              className={styles.action}
              size="sm"
              disabled={isDisabled || !instances?.length}
              isPending={isPending}
              onClick={() => restartQuestHandler()}>
              {t('restart')}
            </Button>
          </Show>
        </Show>

        <Show if={!isDisabled && !isPending && instances?.length && actions?.length}>
          <div className={styles.actions}>
            {questActions?.map((action, idx) => {
              return (
                <Button {...action} className={clsx(styles.action, action.className)} key={idx} />
              )
            })}
          </div>
        </Show>
      </Show>

      <Show if={!isOnTimeStart}>
        <span className={clsx(styles.restricted, styles.soon)}>{t('soon')}</span>
      </Show>

      <Show if={!isOnTimeEnd}>
        <span className={clsx(styles.restricted, styles.ended)}>{t('ended')}</span>
      </Show>
    </>
  )

  const questClassName = clsx(styles.container, {
    // [styles.active]: !isDisabled && instances?.length,
    [styles.custom]: questHref,
    [styles.hasTasks]: tasks?.length,
    [styles.pending]: isPending,
  })

  return (
    <div className={questClassName}>
      <Show if={questHref}>
        <Link href={questHref} className={styles.header}>
          {questContent}
        </Link>
      </Show>
      <Show if={!questHref}>
        <Card className={styles.header}>{questContent}</Card>
      </Show>

      {!!startForm && (
        <Dialog
          type="drawer"
          isOpen={isStartFormOpen}
          className={styles.modal}
          onClose={handleClickClose}>
          <TaskForm
            title={title}
            description={description}
            className={styles.taskForm}
            startForm={startForm ?? ''}
            definitionKey={flowKey}
            onComplete={startQuestHandler}
          />
        </Dialog>
      )}

      {instances?.map((instance) => (
        <QuestInstance
          className={styles.instance}
          key={instance.id}
          flowKey={flowKey}
          img={img}
          instance={instance}
          tasks={tasks}
          reward={reward}
        />
      ))}
    </div>
  )
}
