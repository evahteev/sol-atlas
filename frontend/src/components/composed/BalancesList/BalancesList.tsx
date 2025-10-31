'use client'

import Link from 'next/link'

import { FC } from 'react'

import clsx from 'clsx'

import Message from '@/components/ui/Message'
import Show from '@/components/ui/Show'
import { ChainModel } from '@/models/chain'
import { TokenV3ModelWithBalances } from '@/models/token'

import TokenBalance from '../TokenBalance'

import styles from './BalancesList.module.scss'

type BalancesListProps = {
  className?: string
  chains: ChainModel[]
  data: TokenV3ModelWithBalances[]
}

export const BalancesList: FC<BalancesListProps> = ({ className, chains, data }) => {
  if (!data?.length) {
    return null
  }

  const renderBalancesList = (list: TokenV3ModelWithBalances[], className?: string) => {
    if (!list.length) {
      return null
    }

    return (
      <div className={clsx(styles.content, className)}>
        <ul className={styles.list}>
          {list.map((balance) => (
            <li key={`${balance.id}-${balance.balance}`} className={styles.item}>
              <TokenBalance
                tokenBalance={balance}
                chain={
                  chains?.find((chain) => chain.id === parseInt(balance.chain_id)) ?? {
                    name: 'UNKN',
                  }
                }
              />
            </li>
          ))}
        </ul>
      </div>
    )
  }

  const separatedBalances = data.reduce(
    (acc, curr) => {
      acc[curr.verified ? 'verified' : 'unverified'].push(curr)
      return acc
    },
    { verified: [] as TokenV3ModelWithBalances[], unverified: [] as TokenV3ModelWithBalances[] }
  )

  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.body}>
        {renderBalancesList(separatedBalances.verified, styles.verified)}

        <Show if={separatedBalances.unverified.length}>
          <details className={styles.spoiler}>
            <summary className={styles.spoilerTitle}>Unverified tokens</summary>

            <div className={styles.spoilerBody}>
              <Message type="danger">
                Entering Degen Mode… The tokens below are not on verified token lists, remember to
                DYOR and verify contract addresses.{' '}
                <Link
                  href="https://docs.dex.guru/general/faq#what-is-the-full-degen-mode-inside-the-market-selector"
                  target="_blank"
                  rel="noreferrer noopener">
                  Learn more
                </Link>
              </Message>

              {renderBalancesList(separatedBalances.unverified, styles.unverified)}
            </div>
          </details>
        </Show>
      </div>
    </div>
  )
}
