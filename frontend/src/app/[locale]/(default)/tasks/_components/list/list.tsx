import { FC } from 'react'

import auth from '@/auth'
import { QuestListProps } from '@/components/composed/Quest/QuestList/QuestList'
import { FlowClientObject } from '@/services/flow'

import { PageQuestsListClient } from './client'
import { getFilter } from './utils'

export const PageQuestsList: FC<QuestListProps & { tab?: string }> = async ({ className, tab }) => {
  const session = await auth()
  const flows = await FlowClientObject.flows.list({ filter: getFilter(tab) })

  const [instances, tasks] = session?.access_token
    ? await Promise.all([
        await FlowClientObject.engine.process.instance.list({ session }),
        await FlowClientObject.engine.task.list({ include_history: true, session }),
      ])
    : []
  return (
    <PageQuestsListClient
      tab={tab}
      initialData={{ flows, instances, tasks }}
      className={className}
    />
  )
}
