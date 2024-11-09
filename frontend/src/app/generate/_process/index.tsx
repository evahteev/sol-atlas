'use client'

import { useRouter } from 'next/navigation'

import { useCallback, useEffect, useState } from 'react'
import { FC } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import { useSession } from 'next-auth/react'

import Loader from '@/components/atoms/Loader'
import { ActionPanel } from '@/components/page'
import { Button, Show } from '@/components/ui'
import { FlowClientObject } from '@/services/flow'
import { useProcessInstanceTasks, useProcessInstanceVariables } from '@/services/flow/hooks/engine'

import GeneratedArt from '../components/GeneratedArt/GeneratedArt'

import styles from '../_assets/page.module.scss'

type GenerateProcessProps = {
  prompt: string
  processInstanceId: string
}

const generateArtAndVoteDefinitionKey = 'generate_meme'

export const GenerateProcess: FC<GenerateProcessProps> = ({ prompt, processInstanceId }) => {
  const { data: tasks } = useProcessInstanceTasks(processInstanceId)
  const { data: variables } = useProcessInstanceVariables(processInstanceId)
  const router = useRouter()
  const task = tasks?.find((x) => x.taskDefinitionKey === 'review_modal_season_pass_invite')
  const { data: session } = useSession()
  const [generatedArtId, setGeneratedArtId] = useState<string | null>()

  const [isPending, setIsPending] = useState(false)

  useEffect(() => {
    if (variables?.gen_art_id?.value) {
      setGeneratedArtId(variables?.gen_art_id?.value as string)
    }
  }, [variables?.gen_art_id?.value])

  const onRegenerate = useCallback(async () => {
    if (!task) {
      return
    }

    setGeneratedArtId(null)
    await FlowClientObject.engine.task.complete(task.id, {
      action_regenerate: {
        value: true,
        type: 'Boolean',
        valueInfo: {},
      },
    })
    const tasks = await FlowClientObject.engine.task.list()
    const currentTask = tasks?.find(({ processDefinitionId }) =>
      processDefinitionId?.startsWith('generate_meme')
    )
    if (!currentTask) {
      return
    }
    await FlowClientObject.engine.task.complete(currentTask.id, {
      form_prompt: {
        value: prompt,
        type: 'String',
        valueInfo: {},
      },
    })
  }, [prompt, task])

  const caption = !task || !generatedArtId ? 'Loading...' : 'Post My Meme To Voting'
  const queryClient = useQueryClient()
  const postToVoting = useCallback(async () => {
    if (!task) {
      return
    }

    setIsPending(true)

    const process = await FlowClientObject.engine.process.definitions
      .start('meme_voting', {
        business_key: `${session?.user.id}:${generatedArtId}`,
        variables: {
          gen_art_id: {
            value: generatedArtId,
            type: 'String',
          },
          vote_duration: {
            value: 'PT10080M',
            type: 'String',
          },
        },
      })
      .catch(() => {
        setIsPending(false)
      })

    console.log('vote process started', process)
    await FlowClientObject.engine.task.complete(task.id)
    queryClient.invalidateQueries({
      queryKey: [
        'FlowClientObject.engine.process.instance.list',
        { businessKey: session?.user.id, processDefinitionKey: generateArtAndVoteDefinitionKey },
      ],
    })
    console.log('closed meme generate process')
    router.push(`/gen/${generatedArtId}`)
  }, [generatedArtId, queryClient, router, session?.user.id, task])

  return (
    <>
      <Show if={!generatedArtId}>
        <Loader className={styles.loading} />
      </Show>

      <Show if={generatedArtId}>
        <GeneratedArt generatedArtId={generatedArtId || ''} onRegenerate={onRegenerate} />
      </Show>

      <ActionPanel>
        <Button
          isBlock
          variant="main"
          size="xl"
          disabled={!generatedArtId || !session || isPending}
          isPending={isPending}
          onClick={postToVoting}>
          {caption}
        </Button>
      </ActionPanel>
    </>
  )
}
