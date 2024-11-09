'use client'

import Link from 'next/link'

import { FC, useCallback, useState } from 'react'

import { useQueryClient } from '@tanstack/react-query'
import { get, noop } from 'lodash'
import { useBalance } from 'wagmi'

import Loader from '@/components/atoms/Loader'
import { ActionPanel } from '@/components/page'
import { Burns, Button, Caption, Show } from '@/components/ui'
import { tGuru } from '@/config/wagmi'
import { FlowClientObject } from '@/services/flow'
import { useProcessInstanceVariables } from '@/services/flow/hooks/engine'
import { components } from '@/services/flow/schema'
import { trackButtonClick } from '@/utils/analytics'
import { formatNumber } from '@/utils/numbers'
import { getShortAddress } from '@/utils/strings'

import { OnboardingVariables } from './variables'

import styles from '../_assets/page.module.scss'

const unit = process.env.NEXT_PUBLIC_APP_CURRENCY ?? tGuru.nativeCurrency.symbol

export const OnboardingResult: FC<{
  processInstance: components['schemas']['ProcessInstanceSchema']
  task?: components['schemas']['TaskSchema']
}> = ({ processInstance, task }) => {
  const queryClient = useQueryClient()
  const { queryKey } = useBalance()

  const { data: variables, isLoading } = useProcessInstanceVariables(processInstance?.id)

  const [isPending, setIsPending] = useState(false)

  const txHash = get(variables, 'tx_hash')
  const rewards = get(variables, 'rewards')
  const accountAge = get(variables, 'account_age')
  const premium = get(variables, 'is_premium')

  const submitTaskHandler = useCallback(
    async (taskId: string) => {
      setIsPending(true) // Set claim to pending when user initiates the claim
      trackButtonClick('Button', 'Click', `Claim ${unit} Button`)
      try {
        await FlowClientObject.engine.task.complete(taskId)

        queryClient.invalidateQueries({ queryKey })
        console.log('task completed')
        window.location.href = '/tasks'
      } catch (e) {
        console.error(e)
        setIsPending(false)
      }
    },
    [queryClient, queryKey]
  )

  const isAllowProceed = task && !isPending && !!rewards

  const getButtonLabel = () => {
    if (isAllowProceed) {
      return `Claim my ${unit}!`
    }

    if (!premium) {
      return 'Verifying account...'
    }

    if (!txHash) {
      return 'Transferring...'
    }

    if (!rewards) {
      return 'Calculating...'
    }

    return 'Pending...'
  }

  return (
    <>
      {!isLoading && !!variables && (
        <OnboardingVariables
          isPremium={(premium?.value as boolean) ?? null}
          age={(accountAge?.value as number) ?? null}
        />
      )}

      {(isLoading || !variables || !rewards) && <Loader className={styles.burns} />}

      {!!rewards && (
        <div className={styles.congrats}>
          <Caption variant="header" size="xxl">
            You just got
          </Caption>
          <div className={styles.reward}>
            <Burns variant="numbers" size="xl" className={styles.value}>
              {formatNumber((rewards.value ?? 0) as number)}
            </Burns>

            <Show if={txHash?.value as string | null}>
              <div className={styles.tx}>
                Transaction{' '}
                <Link
                  className={styles.txLink}
                  href={`${tGuru.blockExplorers.default.url}/tx/${txHash?.value}`}
                  target="_blank"
                  rel="noopener noreferrer">
                  {getShortAddress(txHash?.value as string)}
                </Link>
              </div>
            </Show>
          </div>
        </div>
      )}

      <ActionPanel className={styles.actionPanel}>
        <Button
          isBlock
          variant="main"
          size="xl"
          disabled={!isAllowProceed}
          isPending={isPending}
          onClick={isAllowProceed ? () => submitTaskHandler(task?.id) : noop}>
          {getButtonLabel()}
        </Button>
      </ActionPanel>
    </>
  )
}
