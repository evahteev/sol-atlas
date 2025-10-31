'use client'

import { FC, useEffect, useState } from 'react'

import { useQuery } from '@tanstack/react-query'
import clsx from 'clsx'

import Table from '@/components/ui/Table'
import { ChainModel } from '@/models/chain'
import { TransactionModel } from '@/models/history'
import { TokenV3Model } from '@/models/token'
import { TokenTxHistoryParams } from '@/models/tx'

import { historyActivityColumns } from './columns'
import { getRowVars, getTableData, getTotalData } from './helpers'

import styles from './activity.module.scss'

type TokenActivityTableProps = {
  token: TokenV3Model
  initialData?: TransactionModel[]
  className?: string
  params?: TokenTxHistoryParams
  isPaused?: boolean
  chains: ChainModel[]
}

const REFRESH_INTERVAL_SECONDS = 30

export const TokenActivityTable: FC<TokenActivityTableProps> = ({
  token,
  initialData,
  className,
  params,
  isPaused = false,
  chains,
}) => {
  const [tableData, setTableData] = useState<TransactionModel[]>(initialData ?? [])

  const { data, isLoading } = useQuery({
    queryKey: [token, params],
    queryFn: async () => await getTableData(token, params),
    enabled: !isPaused,
    refetchInterval: REFRESH_INTERVAL_SECONDS * 1000,
  })

  useEffect(() => {
    if (!data) {
      return
    }

    setTableData(data || [])
  }, [data])

  const tableUsedData =
    !data && !tableData.length && isLoading ? [...(Array(20) as TransactionModel[])] : tableData

  return (
    <Table
      className={clsx(styles.container, className)}
      classNameTable={styles.table}
      classNameTBody={styles.tbody}
      classNameBody={styles.body}
      rowClassName={styles.trow}
      data={tableUsedData}
      columns={historyActivityColumns(
        token,
        chains.find((chain) => chain.name === token.network),
        getTotalData(tableData)
      )}
      rowProps={(data) => ({
        className: styles.trow,
        'data-loading': !data || undefined,
      })}
      rowVars={getRowVars}
      rowKey={(data, idx) =>
        data
          ? `${data.transactionAddress}-${data.transactionType}-${
              data.type
            }-${data.sender}-${data.to}-${data.fromAddress}-${
              data.toAddress
            }-${data.wallets.join(',')}-${data.poolAddress}-${data.symbols.join(',')}-${
              data.amountsNative
            }-${data.amounts.join(',')}`
          : `${idx}`
      }
    />
  )
}
