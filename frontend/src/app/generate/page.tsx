'use client'

import Image from 'next/image'

import { useCallback, useState } from 'react'

import clsx from 'clsx'
import { useSession } from 'next-auth/react'

import FormField from '@/components/composed/FormField'
import { FormFieldTarget } from '@/components/composed/FormField/FormField'
import { ActionPanel } from '@/components/page'
import { Button, Caption } from '@/components/ui'
import { FlowClientObject } from '@/services/flow'
import { useProcessInstances } from '@/services/flow/hooks/engine'

import { GenerateProcess } from './_process'

import styles from './_assets/page.module.scss'

const generateMemDefinitionKey = 'generate_meme'

const message: Record<string, string> = {
  prompt: 'Enter prompt for your future meme.',
  upload: 'Process with your own meme image.',
}

/**
 * Polls the FlowClientObject to check if the tasks for a specific process instance are available.
 * Continues polling at specified intervals until the task is found or an optional timeout is reached.
 *
 * @param {string} processId - The ID of the process instance to poll for tasks.
 * @param {number} interval - The polling interval in milliseconds (e.g., 1000ms for 1 second).
 * @param {number} [maxWaitTime=0] - Optional maximum wait time in milliseconds. If set to 0 or undefined, polling will continue indefinitely.
 * @returns {Promise<string>} - Resolves with the first task ID when it becomes available.
 * @throws {Error} - If the task is not found within the specified maximum wait time (if defined).
 */
const pollForTasks = async (processId: string, interval: number, maxWaitTime = 0) => {
  // Store the start time to calculate how long we've been polling (only relevant if maxWaitTime is set)
  const startTime = Date.now()

  // Start an infinite loop to repeatedly poll for tasks
  // eslint-disable-next-line no-constant-condition
  while (true) {
    // Attempt to fetch the list of tasks for the given process instance
    const tasks = await FlowClientObject.engine.task.list({
      processInstanceId: processId,
    })

    // If tasks are found and the first task has an ID, return the task ID
    if (tasks.length > 0 && tasks[0].id) {
      return tasks[0].id
    }

    // If maxWaitTime is defined, check if we've exceeded the allowed wait time
    if (maxWaitTime && Date.now() - startTime > maxWaitTime) {
      throw new Error('Task list did not populate within the expected time frame.')
    }

    // Wait for the specified interval before polling again
    await new Promise((resolve) => setTimeout(resolve, interval))
  }
}

export default function GeneratePage() {
  const { data: session } = useSession()
  const { data: instances, isLoading: instancesLoading } = useProcessInstances({
    businessKey: session?.user.id,
    processDefinitionKey: generateMemDefinitionKey,
  })

  const [tab, setTab] = useState<string>('prompt')
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [image, setImage] = useState<any>(null)

  const handleTab = (tab: string) => {
    setTab(tab)
  }

  const uploadImage = (
    target: HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement | null
  ) => {
    if (target === null) {
      return
    }
    const files = (target as HTMLInputElement).files
    if (files) {
      setImage(files[0])
    }
  }

  const generateArtAndVoteProcess = instances?.find(({ definitionId }) =>
    definitionId?.startsWith(generateMemDefinitionKey)
  )

  const [processInstanceId, setProcessInstanceId] = useState<string | undefined>(undefined)
  const [prompt, setPrompt] = useState<string>('')

  const onStartProcess = useCallback(async () => {
    const { id } = await FlowClientObject.engine.process.definitions.start(
      generateMemDefinitionKey,
      {
        variables: {
          form_prompt: {
            value: prompt,
            type: 'String',
          },
        },
      }
    )
    const taskId = await pollForTasks(id, 1000, 0) // Poll every second, no timeout limit

    await FlowClientObject.engine.task.complete(taskId, {
      action_regenerate: {
        value: false,
        type: 'Boolean',
        valueInfo: {},
      },
    })

    setProcessInstanceId(id)
  }, [prompt])

  const generateArtAndVoteId = generateArtAndVoteProcess?.id || processInstanceId || null

  return (
    <>
      <div className={styles.container}>
        {!generateArtAndVoteId && !instancesLoading && (
          <div className={styles.generateContainer}>
            <Caption variant="header" size="lg">
              Generate Your First Meme
            </Caption>
            <div>
              <div className={styles.describeTitle}>Generate coast #1</div>
              <div className={styles.tabs}>
                <span
                  className={clsx(styles.tab, { [styles.active]: tab === 'prompt' })}
                  onClick={() => handleTab('prompt')}>
                  Prompt
                </span>
                <span
                  className={clsx(styles.tab, { [styles.active]: tab === 'upload' })}
                  onClick={() => handleTab('upload')}>
                  Upload
                </span>
              </div>
              <div className={styles.message}>{message[tab]}</div>

              {tab === 'prompt' && (
                <>
                  <FormField
                    autoFocus
                    type="textarea"
                    caption="Describe Your meme"
                    placeholder="old house..."
                    value={prompt}
                    onValueChange={(target: FormFieldTarget) => setPrompt(target?.value ?? '')}
                  />
                </>
              )}

              {tab === 'upload' && (
                <div className={styles.upload}>
                  <div className={styles.uploadContainer}>
                    <div className={styles.uploadRow}>
                      <div className={styles.uploadLabel}>Upload your meme</div>
                      {!image && (
                        <FormField type="file" onValueChange={uploadImage} caption="Choose File" />
                      )}
                    </div>

                    {image && (
                      <Image
                        src={window.URL.createObjectURL(image)}
                        alt=""
                        width={320}
                        height={320}
                        className={styles.uploadImg}
                      />
                    )}
                  </div>

                  {image && (
                    <FormField type="file" onValueChange={uploadImage} caption="Change file" />
                  )}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {!!generateArtAndVoteId && (
        <GenerateProcess prompt={prompt} processInstanceId={generateArtAndVoteId} />
      )}

      {!generateArtAndVoteId && (
        <ActionPanel>
          <Button
            isBlock
            variant="main"
            size="xl"
            disabled={!prompt.length}
            isPending={instancesLoading}
            onClick={onStartProcess}>
            {instancesLoading ? 'Loading...' : 'Generate your own Meme'}
          </Button>
        </ActionPanel>
      )}
    </>
  )
}
