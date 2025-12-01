'use client'

import { useRouter } from 'next/navigation'

import { FC, useCallback, useState } from 'react'

import { useAppKit } from '@reown/appkit/react'
import { useQueryClient } from '@tanstack/react-query'
import { getTransactionCount, sendTransaction, switchChain, writeContract } from '@wagmi/core'
import clsx from 'clsx'
import { toast } from 'react-toastify'
import { Abi, Address, encodeFunctionData } from 'viem'
import { base } from 'viem/chains'
import { useAccount } from 'wagmi'

import { VariablePayload } from '@/actions/engine'
import Loader from '@/components/atoms/Loader'
import TaskForm from '@/components/composed/TaskForm'
import { TaskFormVariable } from '@/components/composed/TaskForm/types'
import Card from '@/components/ui/Card'
import { DEFAULT_REDIRECT_PATH } from '@/config/settings'
import { wagmiAdapter } from '@/config/wagmi'
import IconClose from '@/images/icons/close.svg'
import { FlowClientObject } from '@/services/flow'
import { components } from '@/services/flow/schema'

import styles from './QuestRunner.module.scss'

type QuestTaskRunnerProps = {
  className?: string
  instance: components['schemas']['ProcessInstanceSchema']
  task: components['schemas']['TaskSchema']
  onComplete?: (id?: string, variables?: Record<string, VariablePayload>) => void
  onClose?: () => void
}

export const QuestTaskRunner: FC<QuestTaskRunnerProps> = ({
  className,
  instance,
  task,
  onComplete,
}) => {
  const [isPending, setIsPending] = useState(false)
  const router = useRouter()
  const { address } = useAccount()
  const { open } = useAppKit()
  const queryClient = useQueryClient()
  const taskKey = task?.taskDefinitionKey

  const handleComplete = useCallback(
    async (params?: { businessKey?: string; variables: Record<string, TaskFormVariable> }) => {
      if (!params) {
        onComplete?.()
        return
      }
      const { variables } = params
      setIsPending(true)
      try {
        const formattedVariables: Record<string, VariablePayload> = Object.entries(
          variables
        ).reduce(
          (acc, [key, value]) => {
            acc[key] = {
              ...value,
              valueInfo: value.valueInfo || {}, // Ensure valueInfo is an object
            } as VariablePayload
            return acc
          },
          {} as Record<string, VariablePayload>
        )

        console.log('Sending to API from Task:', formattedVariables) // Debugging output

        // If user didn't cancel txn then go and execute it
        if (
          taskKey?.startsWith('web3Form_') &&
          formattedVariables['action_cancel'].value !== true
        ) {
          if (!address) {
            console.log('wallet is not connected, opening modal..')
            open()
            return
          }
          const requiredFields = [
            'web3_abi',
            'web3_contractAddress',
            'web3_functionName',
            'web3_functionInputs',
            'web3_value',
          ]

          for (const field of requiredFields) {
            if (!formattedVariables[field]) {
              throw new Error(`Missing required field '${field}' in web3Form_ task!`)
            }
          }
          const {
            web3_abi,
            web3_contractAddress,
            web3_functionName,
            web3_functionInputs,
            web3_value,
          } = formattedVariables
          let chainId: number = base.id
          try {
            chainId = parseInt(`${formattedVariables['web3_chainId'].value}`)
          } catch (e) {
            console.error(`Can't get chain id from web3Form task. Fallback to ${chainId}`, e)
          }
          await switchChain(wagmiAdapter.wagmiConfig, {
            chainId,
          })

          if (!address) {
            throw new Error('Connect wallet please!')
          }

          const transactionCount = await getTransactionCount(wagmiAdapter.wagmiConfig, {
            address,
          })
          const functionName = `${web3_functionName.value}`
          const functionInvokeArgs = {
            abi: JSON.parse(`${web3_abi.value}`) as Abi,
            args: JSON.parse(`${web3_functionInputs.value}`),
            functionName,
          } as const

          const isNativeTransfer =
            `${web3_functionInputs.value}` === '[]' &&
            `${web3_abi.value}` === '[]' &&
            functionName === '' &&
            BigInt(`${web3_value.value}`) > 0

          let txData = '0x'
          let txHash = '0x'
          if (isNativeTransfer) {
            txHash = await sendTransaction(wagmiAdapter.wagmiConfig, {
              to: `${web3_contractAddress.value}` as Address,
              value: BigInt(`${web3_value.value}`),
            })
          } else {
            txData = encodeFunctionData(functionInvokeArgs)
            txHash = await writeContract(wagmiAdapter.wagmiConfig, {
              ...functionInvokeArgs,
              address: `${web3_contractAddress.value}` as Address,
              chainId,
              value: BigInt(`${web3_value.value}`),
              nonce: transactionCount,
            })
          }
          formattedVariables['walletAddress'] = {
            type: 'String',
            value: address,
            valueInfo: {},
          }

          formattedVariables['transactionInput'] = {
            type: 'String',
            value: txData,
            valueInfo: {},
          }

          formattedVariables['txHash'] = {
            type: 'String',
            value: txHash,
            valueInfo: {},
          }
        }

        await FlowClientObject.engine.task.complete(task.id, formattedVariables)
        queryClient.invalidateQueries({ queryKey: ['FlowClientObject.engine.task.list'] })

        toast.success('Task completed')
        onComplete?.(task.id, formattedVariables)
      } catch (e) {
        console.error(e)
        toast.error('Error completing task')
      } finally {
        setIsPending(false)
      }
    },
    [address, onComplete, open, queryClient, task.id, taskKey]
  )
  const handleClose = useCallback(async () => {
    try {
      setIsPending(true)

      await FlowClientObject.engine.process.instance.delete(instance.id)
      toast.success('Quest cancelled')
      router.push(DEFAULT_REDIRECT_PATH)
    } catch (e) {
      console.error(e)
      toast.error('Error cancelling Quest')
    } finally {
      setIsPending(false)
    }
  }, [instance.id, router])

  return (
    <Card
      className={clsx(styles.container, className, {
        [styles.active]: !isPending,
        [styles.pending]: isPending,
      })}
      data-process-key={instance.processDefinitionKey}
      data-process-instance={instance.id}
      data-task-key={task.taskDefinitionKey}
      data-task-id={task.id}>
      <button className={styles.close} onClick={handleClose}>
        <IconClose className={styles.closeIcon} />
      </button>
      {!isPending && (
        <TaskForm
          title={task.name}
          description={task.description}
          taskId={task.id}
          definitionKey={instance.processDefinitionKey || ''}
          className={styles.task}
          onComplete={handleComplete}
        />
      )}
      {isPending && <Loader className={styles.loading}>Fetching next step&hellip;</Loader>}
    </Card>
  )
}
