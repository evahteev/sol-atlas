'use server'

import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'
import { TokenTxHistoryParams } from '@/models/tx'

import { getTableData } from './helpers'
import { TokenActivityTable } from './table'

type TokenActivityProps = {
  token: TokenV3Model
  className?: string
  params?: TokenTxHistoryParams
  chains: ChainModel[]
}

export default async function TokenActivity({
  token,
  className,
  params,
  chains,
}: TokenActivityProps) {
  const initialData = await getTableData(token)

  return (
    <TokenActivityTable
      token={token}
      initialData={initialData}
      params={params}
      className={className}
      chains={chains}
    />
  )
}
