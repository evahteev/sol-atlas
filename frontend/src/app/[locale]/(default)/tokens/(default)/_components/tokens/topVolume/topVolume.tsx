'use client'

import Image from 'next/image'

import { FC, useState } from 'react'

import clsx from 'clsx'

import Message from '@/components/ui/Message'
import Table from '@/components/ui/Table'
import { useTokens } from '@/hooks/tokens/useTokens'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'

import { TokensExplorerTableFilter } from '../filter/filter'
import { topVolumeTokenListColumns } from './columns'

import styles from '../assets/styles.module.scss'

type TokensExplorerTopVolumeProps = {
  className?: string
  chains: ChainModel[]
}

const REQUEST_LIMIT = 100

export const TokensExplorerTopVolume: FC<TokensExplorerTopVolumeProps> = ({
  className,
  chains,
}) => {
  const [currentFilter, setCurrentFilter] = useState<Record<string, string>>({})

  const { data, isLoading } = useTokens({
    ids: [],
    network: currentFilter['network'] || chains.map((chain) => chain.name),
    sort_by: 'volume24hUSD',
    order: 'desc',
    field: 'verified',
    value: 'true',
    from_num: 0,
    limit: 20,
  })

  const tableData = [
    ...(data ?? []),
    ...((isLoading ? Array(REQUEST_LIMIT) : []) as TokenV3Model[]),
  ]

  const handleChange = (value: Record<string, string>) => {
    setCurrentFilter(value)
  }

  return (
    <>
      <Message className={styles.comment}>
        Most popular tokens in the past 24 hours based on highest total transaction volume
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
        columns={topVolumeTokenListColumns(chains)}
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
