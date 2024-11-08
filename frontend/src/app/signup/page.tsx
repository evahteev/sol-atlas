'use client'

import { useCallback, useEffect, useState } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import { noop } from 'lodash'
import { useSession } from 'next-auth/react'

import Intro from '@/components/composed/Intro'
import { ActionPanel } from '@/components/page'
import { Button, Caption, Show } from '@/components/ui'
import { tGuru } from '@/config/wagmi'
import { FlowClientObject } from '@/services/flow'
import { useProcessInstances } from '@/services/flow/hooks/engine'
import { components } from '@/services/flow/schema'
import { trackButtonClick } from '@/utils/analytics'

import { OnboardingProcess } from './_onboarding'

import styles from './_assets/page.module.scss'

const onboardingProcessDefinitionKey = 'processUserSignUp'
const unit = process.env.NEXT_PUBLIC_APP_CURRENCY ?? tGuru.nativeCurrency.symbol

export default function PageSignup() {
  const queryClient = useQueryClient()
  const { data: session } = useSession()

  // Move all hooks to the top level
  const [isPending, setIsPending] = useState(false)
  const [processInstance, setProcessInstance] = useState<
    components['schemas']['ProcessInstanceSchema'] | null
  >(null)

  // Conditionally execute the hook logic based on session being available
  const { data: processInstances } = useProcessInstances({
    businessKey: session?.user.id || '',
    processDefinitionKey: onboardingProcessDefinitionKey,
  })

  useEffect(() => {
    setProcessInstance(processInstances?.[0] ?? null)
  }, [processInstances])

  const startOnboarding = useCallback(async () => {
    trackButtonClick('Button', 'Click', 'Start App Button')
    setIsPending(true)
    const process = await FlowClientObject.engine.process.definitions.start(
      onboardingProcessDefinitionKey,
      {
        variables: {
          is_telegram: {
            value: true,
            type: 'Boolean',
          },
        },
      }
    )
    setProcessInstance(process)
    queryClient.invalidateQueries({
      queryKey: ['FlowClientObject.engine.process.instance.list'],
    })
  }, [queryClient])

  if (processInstance) {
    return <OnboardingProcess processInstance={processInstance} />
  }

  return (
    <>
      <Intro className={styles.container}>
        <Caption variant="header" size="md">
          {process.env.NEXT_PUBLIC_APP_INTRO}
        </Caption>
      </Intro>

      <Show if={session}>
        <ActionPanel>
          <Button
            isBlock
            variant="main"
            size="xl"
            onClick={!isPending ? startOnboarding : noop}
            isPending={isPending}>
            {isPending ? 'Analyzing your Telegram...' : `Get initial ${unit}!`}
          </Button>
        </ActionPanel>
      </Show>
    </>
  )
}
