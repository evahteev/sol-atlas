'use client'

import { useCallback, useEffect, useState } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import clsx from 'clsx'
import { useSession } from 'next-auth/react'

import Loader from '@/components/atoms/Loader'
import Meme from '@/components/composed/Meme'
import { Button } from '@/components/ui/Button'
import { Caption } from '@/components/ui/Caption'
import { Show } from '@/components/ui/Show'
import { FlowClientObject } from '@/services/flow'
import { useProcessInstances, useTasks } from '@/services/flow/hooks/engine'
import { useArtNext, useArts } from '@/services/flow/hooks/flow'

import { GenerateQuest } from './_components/generateQuest/GenerateQuest'

import styles from './_assets/page.module.scss'

const generateMemDefinitionKey = 'generate_meme'

export default function GeneratePageNew() {
  const { data: session } = useSession()
  const queryClient = useQueryClient()
  const { data: processInstances, isLoading: isLoadingInstances } = useProcessInstances({
    businessKey: session?.user.id,
    processDefinitionKey: generateMemDefinitionKey,
  })

  const { data: tasks, isLoading: isLoadingTasks } = useTasks(
    {
      processDefinitionKey: generateMemDefinitionKey,
    },
    false
  )

  const { data: myArts, isLoading: isLoadingArts } = useArts(
    session?.user.id ? JSON.stringify({ user__id: session?.user.id }) : undefined
  )
  const { data: arts } = useArtNext({ count: 10 })

  const [processInstanceId, setProcessInstanceId] = useState<string | null>(null)

  const [tab, setTab] = useState<string>('my_memes')

  const handleTab = (tab: string) => {
    setTab(tab)
  }

  const onStartProcess = useCallback(async () => {
    setProcessInstanceId(null)
    const newInstance = await FlowClientObject.engine.process.definitions.start(
      generateMemDefinitionKey,
      {
        variables: {},
      }
    )
    setProcessInstanceId(newInstance.id)
  }, [])

  useEffect(() => {
    queryClient.invalidateQueries({
      queryKey: [
        'FlowClientObject.engine.process.instance.list',
        {
          businessKey: session?.user.id,
          processDefinitionKey: generateMemDefinitionKey,
        },
      ],
    })
    queryClient.invalidateQueries({
      queryKey: [
        'FlowClientObject.engine.task.list',
        {
          processDefinitionKey: generateMemDefinitionKey,
        },
        false,
      ],
    })
  }, [])

  // Use existing process instance if available or start a new one
  useEffect(() => {
    if (processInstances && processInstances.length > 0) {
      setProcessInstanceId(processInstances[0].id)
    } else {
      setProcessInstanceId(null)
    }
  }, [processInstances])

  const isLoading = isLoadingInstances || isLoadingTasks || isLoadingArts

  if (isLoading) {
    return <Loader className={styles.burn} />
  }
  return (
    <div className={styles.container}>
      <Show if={!processInstanceId}>
        <Button
          isBlock
          variant="primary"
          size="xl"
          disabled={false}
          isPending={isLoading}
          onClick={onStartProcess}>
          {isLoading ? 'Loading...' : 'Generate your own Meme'}
        </Button>
      </Show>
      <Show if={processInstanceId}>
        <Caption className={styles.memes__title}>My Draft</Caption>
        <GenerateQuest processInstanceId={processInstanceId!} tasks={tasks!} />
      </Show>
      <div className={styles.memes}>
        <div>
          <div className={styles.tabs}>
            <span
              className={clsx(styles.tab, { [styles.active]: tab === 'my_memes' })}
              onClick={() => handleTab('my_memes')}>
              My memes
            </span>
            <span
              className={clsx(styles.tab, { [styles.active]: tab === 'voting_memes' })}
              onClick={() => handleTab('voting_memes')}>
              Recommended 🔥
            </span>
          </div>

          {tab === 'my_memes' && (
            <ul className={styles.memes__list}>
              {myArts?.map((art, index) => (
                <li key={art.id}>
                  <Meme
                    artId={art.id}
                    rank={index + 1} // Using the index as the rank
                    title={art.name} // Mapping the name to title
                    description={art.description ?? ''} // Adding the description field
                    imageSrc={art.img_picture ?? ''} // Mapping imageSrc to img_picture
                    hasFinances={false} // Always false, since financial info is not available
                  />
                </li>
              ))}
            </ul>
          )}

          {tab === 'voting_memes' && (
            <div className={styles.voting_memes}>
              <ul className={styles.memes__list}>
                {arts?.map((art, index) => (
                  <li key={art.id}>
                    <Meme
                      artId={art.id}
                      rank={index + 1} // Using the index as the rank
                      title={art.name} // Mapping the name to title
                      description={art.description ?? ''} // Adding the description field
                      imageSrc={art.img_picture ?? ''} // Mapping imageSrc to img_picture
                      hasFinances={false} // Always false, since financial info is not available
                    />
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
