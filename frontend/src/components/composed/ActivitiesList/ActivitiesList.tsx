import { FC, useEffect, useState } from 'react'

import clsx from 'clsx'

import { fetchTokens } from '@/actions/tokens'
import Table from '@/components/ui/Table'
import { TableColumnProps } from '@/components/ui/Table/types'
import { ChainModel } from '@/models/chain'
import { TransactionModel } from '@/models/history'
import { TokenV3Model } from '@/models/token'

import { accountActivityColumns } from './columns'
import { getRowVars } from './helpers'

import styles from './ActivitiesList.module.scss'

type ActivitiesListProps = {
  className?: string
  address: string
  chains: ChainModel[]
  data: Partial<TransactionModel>[]
}

export const ActivitiesList: FC<ActivitiesListProps> = ({ className, address, chains, data }) => {
  const [tokens, setTokens] = useState<TokenV3Model[]>([])

  useEffect(() => {
    const allIds = data
      .map((row) =>
        row.tokenAddresses?.map((token) => `${token}-${row.network?.toLocaleLowerCase()}`).flat()
      )
      .filter((id) => !!id)
      .flat()
    const tokenIds = tokens.map((x) => x.id.toLocaleLowerCase())
    const tokenIdsDiff = allIds.filter((x) => x && !tokenIds.includes(x))

    if (tokenIdsDiff.length) {
      fetchTokens({ ids: tokenIdsDiff }).then((res) => {
        if (res?.length) {
          setTokens((prev) => [...prev, ...res])
        }

        setTokens((prev) => [
          ...prev,
          ...tokenIdsDiff.map((id) => {
            const [address, network] = id.split('-')
            return {
              id,
              symbols: ['UNKN'],
              address,
              network,
              name: 'Unknown Token',
            } as TokenV3Model
          }),
        ])
      })
    }
  }, [data, tokens])

  if (!data?.length) {
    return null
  }

  const tableData = data.map((row) => ({
    ...row,
    symbols: (row.tokenAddresses?.map((address) => {
      const chain = chains.find((chain) => chain.name === row.network)
      return tokens.find((token) => token.id === `${address.toLocaleLowerCase()}-${chain?.name}`)
        ?.symbols
    }) ?? ['', '']) as [string, string],
  }))
  const columns: TableColumnProps<Partial<TransactionModel>>[] = accountActivityColumns(address)
  return (
    <div className={clsx(styles.container, className)}>
      <Table
        columns={columns}
        data={tableData}
        className={styles.table}
        rowVars={getRowVars(chains)}
      />
    </div>
  )
}
