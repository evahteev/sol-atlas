'use client'

import { useRouter } from 'next/navigation'

import { useCallback } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import { useSession } from 'next-auth/react'

import { VariablePayload, getTasks } from '@/actions/engine'
import { Caption } from '@/components/ui/Caption'
import { Show } from '@/components/ui/Show'

import { Task } from '../task/Task'

import styles from './Quest.module.scss'

export type GenerateQuestProps = {
  processInstanceId: string
  tasks?: Awaited<ReturnType<typeof getTasks>>
}

const generateMemDefinitionKey = 'generate_meme'

export function GenerateQuest({ tasks }: GenerateQuestProps) {
  const queryClient = useQueryClient()
  const router = useRouter()
  const { data: session } = useSession()

  // const { data: variables, isFetched: isVariablesFetched } = useProcessInstanceVariables(
  //     processInstanceId
  // )
  // const [isPending, setIsPending] = useState(false)

  const handleComplete = useCallback(
    (id?: string, variables?: Record<string, VariablePayload>) => {
      queryClient.invalidateQueries({
        queryKey: ['FlowClientObject.engine.task.list'],
      })
      queryClient.invalidateQueries({
        queryKey: ['FlowClientObject.engine.process.instance.list'],
      })

      if (variables?.action_vote?.value === true && variables?.art_id?.value) {
        queryClient.invalidateQueries({
          queryKey: [
            'FlowClientObject.engine.process.instance.list',
            { businessKey: session?.user.id, processDefinitionKey: generateMemDefinitionKey },
          ],
        })
        router.push(`/gen/${variables.art_id.value}`)
      }
    },
    [queryClient, router, session?.user.id]
  )

  return (
    <div className={styles.container}>
      <Show if={!tasks?.length}>
        <Caption>🔥 Meme creation in progress... 🔥</Caption>
      </Show>
      {tasks?.map((task) => {
        if (task.state === 'ACTIVE') {
          return (
            <Task
              title={task.name}
              description={task.description}
              key={task.id}
              taskKey={task.taskDefinitionKey}
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
