'use client'

import { FC, ReactNode } from 'react'

import clsx from 'clsx'
import { useTranslations } from 'next-intl'

import { questCustomRoute } from '@/components/composed/TaskForm/custom'
import { ButtonProps } from '@/components/ui/Button'
import Message from '@/components/ui/Message'
import { useSession } from '@/hooks/useAuth.compat'
import { FlowClientObject } from '@/services/flow'
import { useProcessInstances, useTasks } from '@/services/flow/hooks/engine'
import { useFlows } from '@/services/flow/hooks/flow'

import { Quest, QuestTypes } from '../Quest'

import styles from './QuestList.module.scss'

export type QuestListProps = {
  unit?: ReactNode
  filter?: {
    flows?: string
  }
  initialData?: {
    flows?: Awaited<ReturnType<typeof FlowClientObject.flows.list>>
    instances?: Awaited<ReturnType<typeof FlowClientObject.engine.process.instance.list>>
    tasks?: Awaited<ReturnType<typeof FlowClientObject.engine.process.instance.task.list>>
  }
  className?: string
  actions?: ButtonProps[] | ((instanceId?: string | null) => ButtonProps[] | null)
}

export const QuestList: FC<QuestListProps> = ({
  initialData,
  filter,
  className,
  unit,
  actions,
}: QuestListProps) => {
  const t = useTranslations('Tasks')
  const { data: session } = useSession()
  const { data: flows } = useFlows({ initialData: initialData?.flows, filter: filter?.flows })
  const { data: instances } = useProcessInstances({
    // initialData: initialData?.instances, //TODO: fix this, leads t stale state between tab switch
    session,
  })
  const { data: tasks } = useTasks({
    // initialData: initialData?.tasks,
    includeHistory: true,
    session,
    query: {
      refetchInterval: 5 * 60 * 1000,
    },
  })

  const renderedQuests = flows?.map((quest) => {
    const questInstances = instances?.filter(
      (instance) => instance.processDefinitionKey === quest.key
    )
    const questTasks = questInstances?.length
      ? questCustomRoute[quest.key]
        ? undefined
        : tasks
            ?.filter((task) => {
              return questInstances
                .map((x) => x.processDefinitionId)
                .some((x) => x === task.processDefinitionId)
            })
            .sort((a) => (a.state === 'COMPLETED' ? 1 : -1))
      : undefined

    return (
      <li className={styles.item} key={quest?.id}>
        <Quest
          title={quest.name}
          description={quest.description ?? undefined}
          isDisabled={!session}
          id={quest.id}
          img={quest.img_picture}
          flowKey={quest.key}
          startForm={quest.start_form || 'none'}
          instances={questInstances}
          tasks={questTasks}
          reward={quest.reward}
          unit={unit}
          type={quest.type as QuestTypes}
          actions={actions}
          start={quest.start}
          end={quest.end}
          url={quest.url}
          startButtonCaption={quest.start_button_text}
        />
      </li>
    )
  })

  const isShowMessage = !renderedQuests?.length

  if (isShowMessage) {
    return <Message type="warn">{t('emptyState')}</Message>
  }

  if (!renderedQuests?.length) {
    return null
  }

  return (
    <div className={clsx(styles.container, className)}>
      <ul className={styles.list}>{renderedQuests}</ul>
    </div>
  )
}
