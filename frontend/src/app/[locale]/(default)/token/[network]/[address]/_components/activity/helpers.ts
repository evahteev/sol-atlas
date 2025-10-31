import { fetchTokenTxHistoryLast } from '@/actions/tokens'
import { TransactionModel } from '@/models/history'
import { TokenV3Model } from '@/models/token'
import { TokenTxHistoryParams } from '@/models/tx'

export const getTableData = (token: TokenV3Model, params: TokenTxHistoryParams = {}) =>
  fetchTokenTxHistoryLast(token.id, params)

export const getTotalData = (
  data: TransactionModel[]
): { min: number; max: number; total: number } =>
  data?.reduce(
    (acc, row) => ({
      min: Math.min(acc.min || row?.amountStable || 0, row?.amountStable || 0),
      max: Math.max(acc.max, row?.amountStable || 0),
      total: acc.total + (row?.amountStable || 0),
    }),
    { min: 0, max: 0, total: 0 }
  )

export type RowVarsProps = {
  outAmounts?: number[]
  outTokenAddresses?: string[]
  outTokenSymbols?: string[]
  outAddress?: string
  inAmounts?: number[]
  inToken?: string
  inTokenAddresses?: string[]
  inTokenSymbols?: string[]
  inAddress?: string
}

export const getRowVars = (data?: TransactionModel): RowVarsProps => {
  const result: RowVarsProps = {}

  if (!data) {
    return result
  }

  if (['swap', 'transfer'].includes(data?.transactionType || '')) {
    const indexFrom =
      data?.transactionType === 'swap' ? data?.tokenAddresses.indexOf(data?.fromAddress) : 0
    const indexTo =
      data?.transactionType === 'swap' ? data?.tokenAddresses.indexOf(data?.toAddress) : 0

    if (indexFrom === -1 || indexTo === -1) {
      return result
    }

    result.outAddress = data?.tokenAddresses[indexFrom]
    result.outAmounts = [data?.amounts[indexFrom]]
    result.outTokenAddresses = [data?.tokenAddresses[indexFrom]]
    result.outTokenSymbols = [data?.symbols[indexFrom]]
    result.inAddress = data?.tokenAddresses[indexTo]
    result.inAmounts = [data?.amounts[indexTo]]
    result.inTokenAddresses = [data?.tokenAddresses[indexTo]]
    result.inTokenSymbols = [data?.symbols[indexTo]]
  }

  if (['burn', 'mint'].includes(data.transactionType)) {
    const isBurn = data.transactionType === 'burn'
    result[isBurn ? 'inTokenSymbols' : 'outTokenSymbols'] = data.symbols
    result[isBurn ? 'inTokenAddresses' : 'outTokenAddresses'] = data.tokenAddresses
    result[isBurn ? 'inAmounts' : 'outAmounts'] = data.amounts
    result.outAddress = data.sender ?? data.poolAddress
    result.inAddress = data.to ?? data.wallets?.[0]
  }

  return result
}
