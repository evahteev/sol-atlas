'use client'

import { FC, useCallback, useState } from 'react'

import { useAppKit } from '@reown/appkit/react'
import { useQueryClient } from '@tanstack/react-query'
import { getTransactionCount, sendTransaction, switchChain, writeContract } from '@wagmi/core'
import clsx from 'clsx'
import DOMPurify from 'isomorphic-dompurify'
import noop from 'lodash/noop'
import { marked } from 'marked'
import { toast } from 'react-toastify'
import { Abi, Address, encodeFunctionData } from 'viem'
import { base } from 'viem/chains'
import { useAccount, useBalance } from 'wagmi'

import { VariablePayload } from '@/actions/engine'
import TaskForm from '@/components/composed/TaskForm'
import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'
import Dialog from '@/components/ui/Dialog'
import Show from '@/components/ui/Show'
import { wagmiAdapter } from '@/config/wagmi'
import IconRight from '@/images/icons/chevron-right.svg'
import { FlowClientObject } from '@/services/flow'
import { components } from '@/services/flow/schema'

import styles from './QuestTask.module.scss'

type QuestTaskProps = {
  task: components['schemas']['TaskSchema']
  icon?: string | null
  definitionKey: string
  onComplete?: (id?: string, variables?: Record<string, VariablePayload>) => void
  className?: string
}

export const QuestTask: FC<QuestTaskProps> = ({
  task,
  icon,
  definitionKey,
  onComplete,
  className,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isPending, setIsPending] = useState(false)
  const { address } = useAccount()
  const { open } = useAppKit()
  const queryClient = useQueryClient()
  const { queryKey: balanceQueryKey } = useBalance()

  const handleClickClose = useCallback(() => {
    setIsOpen(false)
  }, [])

  const handleClickOpen = useCallback(() => {
    setIsOpen(true)
  }, [])

  const handleComplete = useCallback(
    async (params?: {
      businessKey?: string
      variables: Awaited<ReturnType<typeof FlowClientObject.engine.task.variables.list>>
    }) => {
      if (!params) {
        onComplete?.()
        return
      }
      const { variables } = params
      setIsPending(true)

      handleClickClose()
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
          task?.taskDefinitionKey?.startsWith('web3Form_') &&
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

        queryClient.invalidateQueries({ queryKey: balanceQueryKey })
        toast.success('Task completed')
        onComplete?.(task.id, formattedVariables)
      } catch (e) {
        console.error(e)
        toast.error('Error completing task')
      } finally {
        setIsPending(false)
      }
    },
    [handleClickClose, onComplete, task, queryClient, balanceQueryKey, address, open]
  )

  const parsedMarkup = DOMPurify.sanitize(
    marked.parse(task.description ?? '', {
      async: false,
    }) as string
  )

  return (
    <>
      <Card
        title={task.id}
        className={clsx(
          styles.container,
          {
            [styles.active]: !isPending,
            [styles.pending]: isPending,
          },
          className
        )}
        onClick={!isOpen && !isPending ? handleClickOpen : noop}
        tabIndex={0}>
        <div className={styles.body}>
          <Caption variant="body" size="sm" strong className={styles.title}>
            {task.name}
          </Caption>
          <Show if={task.description}>
            <Caption
              size="xs"
              className={styles.subtitle}
              dangerouslySetInnerHTML={{ __html: parsedMarkup }}
            />
          </Show>
        </div>
        <div className={styles.footer}>
          <IconRight className={styles.icon} />
        </div>
      </Card>

      <Dialog type="drawer" isOpen={isOpen} className={styles.modal} onClose={handleClickClose}>
        <TaskForm
          title={task.name}
          description={task.description}
          taskId={task.id}
          className={styles.taskForm}
          icon={icon}
          definitionKey={definitionKey}
          onComplete={handleComplete}
        />
      </Dialog>
    </>
  )
}
