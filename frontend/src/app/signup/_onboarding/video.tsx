'use client'

import { FC, useState } from 'react'

import { noop } from 'lodash'

import Loader from '@/components/atoms/Loader'
import { ActionPanel } from '@/components/page'
import { Button, Show } from '@/components/ui'
import Message from '@/components/ui/Message'
import { FlowClientObject } from '@/services/flow'
import { useTaskVariables } from '@/services/flow/hooks/engine'
import { components } from '@/services/flow/schema'
import { trackButtonClick } from '@/utils/analytics'

import styles from '../_assets/page.module.scss'

export const OnboardingProcessVideo: FC<{
  task: components['schemas']['TaskSchema']
}> = ({ task }) => {
  const [isPending, setIsPending] = useState(false)

  const { data: variables, isLoading } = useTaskVariables(task.id)

  const video = (variables?.video_filePath?.value as string) ?? ''

  const handleTaskSubmit = async (taskId: string) => {
    setIsPending(true) // Set claim to pending when user initiates the claim
    trackButtonClick('Button', 'Click', 'Start Burn Button')
    try {
      await FlowClientObject.engine.task.complete(taskId)

      console.log('task completed')
      window.location.href = '/tasks'
    } catch (e) {
      console.error(e)
      setIsPending(false)
    }
  }

  return (
    <>
      <Show if={isLoading}>
        <Loader className={styles.burns} />
      </Show>

      <Show if={!isLoading && variables && video}>
        <video
          controls
          controlsList="nofullscreen nodownload noremoteplayback noplaybackrate"
          autoPlay
          muted
          loop
          className={styles.video}
          src={video}
        />
      </Show>

      <Show if={!isLoading && !variables && !video}>
        <Message type="danger">Unexpected error. You can just proceed.</Message>
      </Show>

      <ActionPanel className={styles.actionPanel}>
        <Button
          isBlock
          variant="main"
          size="xl"
          disabled={isLoading || isPending}
          isPending={isPending}
          onClick={!isLoading && !isPending ? () => handleTaskSubmit(task.id) : noop}>
          <Show if={isLoading}>Loading...</Show>
          <Show if={!isLoading}>
            {(variables?.action_startBurn?.label as string) || 'Start Burn'}
          </Show>
        </Button>
      </ActionPanel>
    </>
  )
}
