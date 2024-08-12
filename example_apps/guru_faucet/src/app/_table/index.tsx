'use client'

import { FC, useCallback, useEffect, useMemo, useState } from 'react'

import { useWeb3Modal } from '@web3modal/wagmi/react'
import { useDebounceFn } from 'rooks'
import { useAccount } from 'wagmi'

import Button from '@/components/Button'
import Table from '@/components/Table'
import { tGuru } from '@/config/wagmi'
import FlowClient from '@/services/flow/client'

import CountdownTimer from '../_process-state/_countdown'
import { useSeasonPassInvite } from '../_process-state/hooks'

import styles from './table.module.scss'

type SeasonPassFaucetTableProps = {
  className?: string
}

const processDefinitionKey = 'automation_faucet'

export const SeasonPassFaucetTable: FC<SeasonPassFaucetTableProps> = ({ className }) => {
  const { address } = useAccount()
  const { open } = useWeb3Modal()
  const [isDisabled, setIsDisabled] = useState(false)

  const { processInstance, tasks, isFetched } = useSeasonPassInvite(processDefinitionKey)

  useEffect(() => {
    setIsDisabled(!!processInstance)
  }, [processInstance])

  const startFaucetProcess = useCallback(() => {
    const flowClient = new FlowClient()
    const variables = {
      wallet_address: {
        type: 'String' as const,
        value: address,
        valueInfo: {},
      },
    }
    flowClient.startProcessInstanceByKey(processDefinitionKey, {
      variables,
    })
  }, [address])

  const [startFaucetProcessDebounced] = useDebounceFn(startFaucetProcess, 60 * 60 * 1000, {
    leading: true,
  })

  const txHash = useMemo(
    () => processInstance?.variables.find((x) => x.name === 'tx_hash')?.value,
    [processInstance]
  )

  const successProcessEndTask = useMemo(
    () =>
      tasks?.find(
        (x) =>
          x.taskDefinitionKey === 'success_form' &&
          x.processDefinitionId.includes(processDefinitionKey)
      ),
    [tasks]
  )

  const bpmnError = useMemo(
    () => tasks?.find((x) => x.taskDefinitionKey === 'error_user_task'),
    [tasks]
  )

  const nextClaimDate = useMemo(
    () =>
      (processInstance?.variables.find((x) => x.name === 'next_faucet_date_iso')
        ?.value as string) || undefined,
    [processInstance?.variables]
  )

  const tableTitle = (
    <div className={styles.header}>
      <span>Daily quest</span> <span className={styles.comment}>Refresh every 24 hours</span>{' '}
      {successProcessEndTask && nextClaimDate && (
        <span className={styles.timer}>
          <CountdownTimer
            prefix="Come back after"
            futureTimestamp={nextClaimDate}
            suffix="to get more tGURU!"
          />
        </span>
      )}
    </div>
  )

  return (
    <>
      <Table
        className={className}
        title={bpmnError ? 'Something went wrong. Try in a minute' : tableTitle}
        showHeader={false}
        columns={[
          { render: ({ data }) => data.title, className: styles.caption },
          { render: ({ data }) => <span className={styles.comment}>{data.descriptions}</span> },
          {
            type: 'number',
            render: ({ data }) => {
              const txHashLink = data?.txHash
                ? `${tGuru.blockExplorers.default.url}/tx/${data.txHash}`
                : undefined

              if (txHashLink) {
                return (
                  <Button
                    size="lg"
                    href={txHashLink}
                    target="_blank"
                    rel="noopener noreferrer"
                    variant="primary">
                    View tx
                  </Button>
                )
              }

              const isChecking = !isFetched && !data?.processInstance

              if (!data?.active) {
                return (
                  <Button size="lg" variant="primary" isDisabled>
                    Coming soon
                  </Button>
                )
              }

              if (isChecking || !!data?.processInstance) {
                return (
                  <Button size="lg" variant="primary" isDisabled isPending>
                    {isChecking ? 'Checking Availability' : 'Processing…'}
                  </Button>
                )
              }

              if (!data?.onClick || isDisabled) {
                return (
                  <Button size="lg" variant="primary" isDisabled>
                    Claim
                  </Button>
                )
              }

              return (
                <Button
                  size="lg"
                  variant="primary"
                  disabled={isDisabled}
                  onClick={(e) => {
                    if (!address) {
                      open()
                      return
                    }
                    const target = e.target as HTMLButtonElement
                    target.disabled = true
                    setIsDisabled(true)
                    data?.onClick()
                  }}>
                  Claim
                </Button>
              )
            },
          },
        ]}
        data={[
          {
            title: 'Claim 10 tGURU',
            descriptions: 'For free daily',
            active: true,
            onClick: () => {
              startFaucetProcessDebounced()
            },
            processInstance,
            txHash,
          },
          {
            title: 'Claim 10 tGURU',
            descriptions: 'For Retweet',
          },
          {
            title: 'Claim 10 tGURU',
            descriptions: 'For Recast',
          },
        ]}
      />

      <Table
        className={className}
        title="Bonus quest"
        showHeader={false}
        columns={[
          { render: ({ data }) => data.title },
          {
            type: 'number',
            render: () => (
              <Button size="lg" caption="Coming soon" disabled={true} variant="primary" />
            ),
          },
        ]}
        data={[
          {
            title: 'Get a bonus for a 10 day streak – 30 tGURU',
          },
          {
            title: 'Join Discord Channel for 20 tGURU',
          },
          {
            title: 'Join Telegram Channel for 20 tGURU',
          },
          {
            title: 'Follow us on X/Twitter for 20 tGURU',
          },
          {
            title: 'Follow us on Farcaster for 20 tGURU',
          },
          {
            title: 'Subscribe for Email for 20 tGURU',
          },
        ]}
      />
    </>
  )
}
