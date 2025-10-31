'use client'

import Image from 'next/image'

import { FC, useState } from 'react'

import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'

import { fetchTokensTrending } from '@/actions/tokens'
import Message from '@/components/ui/Message'
import Table from '@/components/ui/Table'
import { ChainModel } from '@/models/chain'
import { TrendingToken } from '@/models/token'

import { TokensExplorerTableFilter } from '../filter/filter'
import { trendingTokenListColumns } from './columns'

import styles from '../assets/styles.module.scss'

type TokensExplorerTrendingProps = {
  className?: string
  chains: ChainModel[]
}

const REQUEST_LIMIT = 100

export const TokensExplorerTrending: FC<TokensExplorerTrendingProps> = ({ className, chains }) => {
  const [currentFilter, setCurrentFilter] = useState<Record<string, string>>({})
  const { data, isLoading } = useQuery({
    queryKey: ['fetchTokensTrending', currentFilter['network']],
    queryFn: () =>
      fetchTokensTrending({
        network: currentFilter['network'] || chains.map((chain) => chain.name),
      }),
  })

  const tableData = [
    ...(data ?? []),
    ...((isLoading ? Array(REQUEST_LIMIT) : []) as TrendingToken[]),
  ]

  const handleChange = (value: Record<string, string>) => {
    setCurrentFilter(value)
  }

  return (
    <>
      <Message className={styles.comment}>
        Trending tokens in the past 24 hours based on activity & volume from Whales (Traders with
        &gt;$500k of a trading volume over the last 30 day)
      </Message>

      <TokensExplorerTableFilter
        fields={{
          network: {
            options: [
              { value: '', label: 'Any network' },
              ...chains.map((chain) => ({
                value: chain.name,
                label: chain.description,
                icon: (
                  <Image
                    src={chain.logo_uri ?? ''}
                    width={32}
                    height={32}
                    className={styles.icon}
                    alt={chain.name}
                  />
                ),
              })),
            ],
          },
        }}
        onChange={handleChange}
      />

      <Table
        columns={trendingTokenListColumns(chains)}
        data={tableData}
        className={clsx(styles.wrapper, className)}
        classNameTable={styles.table}
        classNameTBody={styles.tbody}
        classNameBody={styles.body}
        rowClassName={styles.trow}
        rowHref={(rowData) => {
          if (!rowData || rowData?.network === 'solana') {
            return null
          }

          return `/token/${rowData?.network?.toLocaleLowerCase()}/${rowData?.tokenAddress?.toLocaleLowerCase()}?view=trending`
        }}
        rowKey={(data) => data?.id}
        rowProps={(data) => ({
          'data-loading': !data || undefined,
        })}
      />
    </>
  )
}
