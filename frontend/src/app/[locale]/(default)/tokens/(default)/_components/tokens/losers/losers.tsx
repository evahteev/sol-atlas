'use client'

import Image from 'next/image'

import { FC, useState } from 'react'

import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'

import { fetchTokensLosers } from '@/actions/tokens'
import Message from '@/components/ui/Message'
import Table from '@/components/ui/Table'
import { ChainModel } from '@/models/chain'
import { TokenV2Model } from '@/models/token'

import { TokensExplorerTableFilter } from '../filter/filter'
import { gainersTokenListColumns } from './columns'

import styles from '../assets/styles.module.scss'

type TokensExplorerLosersProps = {
  className?: string
  chains: ChainModel[]
}

const REQUEST_LIMIT = 100

export const TokensExplorerLosers: FC<TokensExplorerLosersProps> = ({ className, chains }) => {
  const [currentFilter, setCurrentFilter] = useState<Record<string, string>>({})
  const { data, isLoading } = useQuery({
    queryKey: ['fetchTokensLosers', currentFilter['network']],
    queryFn: () => {
      return fetchTokensLosers({
        network: currentFilter['network'] || chains.map((chain) => chain.name),
        limit: 20,
        offset: 0,
      })
    },
  })

  const tableData = [
    ...(data ?? []),
    ...((isLoading ? Array(REQUEST_LIMIT) : []) as TokenV2Model[]),
  ]

  const handleChange = (value: Record<string, string>) => {
    setCurrentFilter(value)
  }

  return (
    <>
      <Message className={styles.comment}>
        Worst performing tokens in the past 24 hours by % loss with transaction
        volume&nbsp;&gt;$50,000
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
        columns={gainersTokenListColumns(chains)}
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

          return `/token/${rowData?.network.toLocaleLowerCase()}/${rowData?.address.toLocaleLowerCase()}?view=trending`
        }}
        rowKey={(data) => data?.id}
        rowProps={(data) => ({
          'data-loading': !data || undefined,
        })}
      />
    </>
  )
}
