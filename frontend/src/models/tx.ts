export type TokenTxType = 'mint' | 'burn' | 'swap' | 'transfer'

export type TokenTxHistoryParams = {
  sort_by?: 'timestamp'
  limit?: number
  offset?: 0
  order?: 'desc'
  with_full_totals?: boolean
  transaction_types?: TokenTxType[]
  token_status?: 'all'

  account?: string
  amm?: string
  date?: { start_date: number; end_date: number }
  trade_size_usd?: { amount: number; operator: 'gt' | 'lt' | 'equal' }
}
