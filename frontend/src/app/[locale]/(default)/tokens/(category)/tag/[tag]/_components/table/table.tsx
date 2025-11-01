'use client'

import Link from 'next/link'

import { FC } from 'react'

import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'

import { fetchTokenProfiles } from '@/actions/tokens'
import Caption from '@/components/ui/Caption'
import Stats from '@/components/ui/Stats'
import Table from '@/components/ui/Table'
import IconBack from '@/images/icons/chevron-left.svg'
import { ChainModel } from '@/models/chain'
import { TokenProfile, TokenTagModel } from '@/models/token'
import { getChainByName } from '@/utils/chains'

import { TokensExplorerTableDistribution } from './chart/pie/distribution'
import { tokenListColumns } from './columns'

import styles from './table.module.scss'

type TokensExplorerTableProps = {
  tag: TokenTagModel
  className?: string
  chains: ChainModel[]
}

const REQUEST_LIMIT = 100

export const TokensExplorerTable: FC<TokensExplorerTableProps> = ({ tag, className, chains }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['fetchTokenProfiles', tag.id],
    queryFn: () =>
      fetchTokenProfiles({
        tags: [tag.id],
        limit: REQUEST_LIMIT,
        offset: 0,
      }),
  })

  const tableData = [
    ...(data ?? []),
    ...((isLoading ? Array(REQUEST_LIMIT) : []) as TokenProfile[]),
  ]

  const fdvDistribution =
    data?.reduce(
      (acc, curr) => {
        if (!acc[curr.network]) {
          const chain = getChainByName(chains, curr.network)

          acc[curr.network] = {
            value: 0,
            name: chain?.description ?? 'Unknown',
            color: chain?.color ?? 'grey',
          }
        }

        acc[curr.network].value += curr.fully_diluted_valuation

        return acc
      },
      {} as Record<string, { value: number; name: string; color: string }>
    ) ?? {}

  return (
    <>
      <Caption variant="header" size="lg" className={styles.title}>
        <Link href="/tokens" className={styles.backLink}>
          <IconBack className={styles.icon} />
        </Link>

        <span className={styles.caption}>{tag.tag_name}</span>
      </Caption>

      <Stats
        items={[
          {
            title: 'FDV by Network',
            content: (
              <TokensExplorerTableDistribution
                data={Object.values(fdvDistribution)}
                className={styles.statChart}
              />
            ),
          },
        ]}
      />

      <Table
        columns={tokenListColumns(chains)}
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

          return `/token/${rowData?.network.toLocaleLowerCase()}/${rowData?.token_address.toLocaleLowerCase()}?tag=${tag.id}`
        }}
        rowKey={(data) => data?.id}
        rowProps={(data) => ({
          'data-loading': !data || undefined,
        })}
      />
    </>
  )
}
