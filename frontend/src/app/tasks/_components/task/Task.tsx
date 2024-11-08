'use client'

import { FC, useCallback, useState } from 'react'

import { base } from '@reown/appkit/networks'
import { useAppKit } from '@reown/appkit/react'
import { useQueryClient } from '@tanstack/react-query'
import { getTransactionCount, switchChain, writeContract } from '@wagmi/core'
import clsx from 'clsx'
import { noop } from 'lodash'
import { toast } from 'react-toastify'
import { Abi, encodeFunctionData } from 'viem'
import { useAccount, useBalance } from 'wagmi'

import { VariablePayload, getTaskVariables } from '@/actions/engine'
import { Caption, Card, Show } from '@/components/ui'
import Dialog from '@/components/ui/Dialog'
import { wagmiAdapter } from '@/config/wagmi'
import IconRight from '@/images/icons/chevron-right.svg'
import { FlowClientObject } from '@/services/flow'
import { trackButtonClick } from '@/utils/analytics'

import { TaskForm } from './TaskForm'

import styles from './Task.module.scss'

type TaskProps = {
  title: string
  icon?: string | null
  description?: string | null
  id: string
  taskKey?: string | null
  flowKey: string
  onComplete?: (id?: string, variables?: Record<string, VariablePayload>) => void
}

const SPOOKY_NFT_CONTRACT = '0x0902372C13ae4AC73efE30AF3911D20F31Bdfe33'

export const Task: FC<TaskProps> = ({
  title,
  icon,
  id,
  taskKey,
  flowKey,
  onComplete,
  description,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const [isPending, setIsPending] = useState(false)
  const { address } = useAccount()
  const { open } = useAppKit()
  const queryClient = useQueryClient()
  const { queryKey } = useBalance()

  const handleClickClose = useCallback(() => {
    trackButtonClick('Button', 'Click', 'Close task Button')
    setIsOpen(false)
  }, [])

  const handleClickOpen = useCallback(() => {
    trackButtonClick('Button', 'Click', 'Open task Button')
    setIsOpen(true)
  }, [])

  const handleComplete = useCallback(
    async (variables: Awaited<ReturnType<typeof getTaskVariables>>) => {
      setIsPending(true)

      trackButtonClick('Task', 'Complete task Button', title)

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

        if (taskKey?.startsWith('web3Form_')) {
          if (!address) {
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
          const { web3_abi, web3_contractAddress, web3_functionName, web3_value } =
            formattedVariables
          await switchChain(wagmiAdapter.wagmiConfig, {
            chainId: base.id,
          })

          if (!address) {
            throw new Error('Connect wallet please!')
          }

          const transactionCount = await getTransactionCount(wagmiAdapter.wagmiConfig, {
            address,
          })
          const functionName = web3_functionName.value.toString()
          const functionInvokeArgs = {
            abi: JSON.parse(web3_abi.value.toString()) as Abi,
            args:
              functionName === 'safeMint'
                ? [address]
                : [SPOOKY_NFT_CONTRACT, BigInt(500 * 10 ** 18)],
            functionName,
          } as const

          const txData = encodeFunctionData(functionInvokeArgs)
          const txHash = await writeContract(wagmiAdapter.wagmiConfig, {
            ...functionInvokeArgs,
            address: web3_contractAddress.value.toString() as `0x${string}`,
            chainId: base.id,
            value: BigInt(web3_value.value.toString()),
            nonce: transactionCount,
          })

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

        await FlowClientObject.engine.task.complete(id, formattedVariables)

        queryClient.invalidateQueries({ queryKey })
        toast.success('Task completed')
        onComplete?.(id, formattedVariables)
      } catch (e) {
        console.error(e)
        toast.error('Error completing task')
      } finally {
        setIsPending(false)
      }
    },
    [title, handleClickClose, taskKey, id, queryClient, queryKey, onComplete, address, open]
  )

  return (
    <>
      <Card
        className={clsx(styles.container, {
          [styles.active]: !isPending,
          [styles.pending]: isPending,
        })}
        onClick={!isOpen && !isPending ? handleClickOpen : noop}>
        <div className={styles.body}>
          <Caption variant="body" size="sm" strong className={styles.title}>
            {title}
          </Caption>
          <Show if={description}>
            <Caption size="xs" className={styles.subtitle}>
              {description}
            </Caption>
          </Show>
        </div>
        <div className={styles.footer}>
          <IconRight className={styles.icon} />
        </div>

        <Dialog isOpen={isOpen} className={styles.modal} onClose={handleClickClose}>
          <TaskForm
            title={title}
            icon={icon}
            id={id}
            flowKey={flowKey}
            taskKey={taskKey}
            onComplete={handleComplete}
          />
        </Dialog>
      </Card>
    </>
  )
}
