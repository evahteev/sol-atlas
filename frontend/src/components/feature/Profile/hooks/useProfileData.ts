import { CaipAddress } from '@reown/appkit'
import { env } from 'next-runtime-env'

import useNftBalances from '@/hooks/useNftBalances'
import { useWalletTotals } from '@/hooks/useWalletTotals'
import { useQueryResponse } from '@/hooks/warehouse/useQueryResponse'
import { ChainModel } from '@/models/chain'
import { TransactionModel } from '@/models/history'

const contracts: CaipAddress[] = JSON.parse(env('NEXT_PUBLIC_APP_COMMUNITY_NFT_ADDRESSES') || '[]')

export const useProfileData = ({
  address,
  chains,
  refetchInterval,
}: {
  address?: string | null
  chains: ChainModel[]
  refetchInterval?: number
}) => {
  const {
    tokens,
    natives,
    isFetching: isFetchingBalances,
    isFetchingNative,
    isFetchingTokens,
    refetch: refetchTotals,
  } = useWalletTotals({ address, chains, refetchInterval, enabled: !!address })

  const balances = [...tokens, ...natives].sort(
    (a, b) => (b.balance || 0) * (b.priceUSD || 0) - (a.balance || 0) * (a.priceUSD || 0)
  )
  const totalValue = balances.reduce(
    (acc, token) => acc + (token.balance || 0) * (token.priceUSD || 0),
    0
  )

  const {
    result: actionsResult,
    isFetching: isFetchingActions,
    refetch: refetchActions,
  } = useQueryResponse({
    queryId: 'wallet_actions',
    params: {
      offset: 0,
      limit: 100,
      wallet_address: address,
    },
    maxAge: 0,
    refetchInterval,
  })

  const actions: Partial<TransactionModel>[] =
    actionsResult?.data.rows.map((row) => {
      return {
        // type: string
        network: chains.find((chain) => `${chain.id}` === `${row.chain_id}`)?.name,
        timestamp: Number(row.block_timestamp),
        transactionType: `${row.transaction_type}`,
        transactionAddress: `${row.transaction_hash}`,
        tokenAddresses: row.token_addresses as [string, string],
        // symbols: [string, string]
        wallets: row.wallets as [string, string],
        // walletsCategories: [string, string]
        amounts: row.amounts as [number, number],
        amountStable: row.amount_stable as number,
        amountNative: row.amount_native as number,
        // amountsStable: [number, number]
        // amountsNative: [number, number]
        // pricesStable: [number, number]
        // pricesNative: [number, number]
        // poolAddress: string
        // fromAddress: string
        // toAddress: string
        // lpToken: null
        // sender: string
        // to: string
      }
    }) ?? []

  const {
    data: nfts,
    refetch: refetchNftBalances,
    isFetching: isFetchingNftBalances,
  } = useNftBalances({ contracts, address, refetchInterval })
  const totalNftCount =
    nfts?.reduce((acc, collection) => acc + (collection?.nftBalance?.length || 0), 0) ?? 0

  const refetch = () => {
    refetchTotals()
    refetchActions()
    refetchNftBalances()
  }

  return {
    tokens,
    natives,
    balances,
    totalValue,
    actions,
    nfts,
    totalNftCount,
    isFetching: isFetchingBalances || isFetchingActions || isFetchingNftBalances,
    isFetchingBalances,
    isFetchingNative,
    isFetchingTokens,
    isFetchingActions,
    isFetchingNftBalances,
    refetch,
  }
}
