import { useCallback, useContext, useEffect, useMemo, useState } from 'react'

import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { fetchTokens, getErc20Balances, getNativeBalances } from '@/actions/tokens'
import { CustomToken } from '@/components/composed/TaskForm/custom/swapToken/types'
import { useQueryResponse } from '@/hooks/warehouse/useQueryResponse'
import { ChainModel } from '@/models/chain'
import { TokenV3Model, TokenV3ModelWithBalances, WalletTokenBalance } from '@/models/token'
import { AppContext } from '@/providers/context'
import { mapGuruNetworkToChainId } from '@/utils/chains'

const ERC_20_TOKENS_RPC: CustomToken[] = [
  {
    id: '0x525574c899a7c877a11865339e57376092168258-eth',
    address: '0x525574c899a7c877a11865339e57376092168258',
    name: 'GURU',
    symbols: ['GURU'],
    logoURI: [null],
    decimals: 18,
    network: 'eth',
  },
]

export const useWalletTotals = ({
  address,
  chains,
  erc20Tokens = ERC_20_TOKENS_RPC,
  refetchInterval,
  enabled = true,
  initialData,
}: {
  address?: string | null
  chains: ChainModel[]
  erc20Tokens?: CustomToken[]
  refetchInterval?: number
  enabled?: boolean
  initialData?: {
    tokens?: TokenV3ModelWithBalances[]
    natives?: TokenV3ModelWithBalances[]
  }
}) => {
  const {
    config: { staking },
  } = useContext(AppContext)
  const { token: stakingToken, rewardToken } = staking || {}
  if (stakingToken && !ERC_20_TOKENS_RPC.some((x) => x.id === stakingToken.id)) {
    ERC_20_TOKENS_RPC.push(stakingToken)
  }
  if (rewardToken && !ERC_20_TOKENS_RPC.some((x) => x.id === rewardToken.id)) {
    ERC_20_TOKENS_RPC.push(rewardToken)
  }
  const [tokens, setTokens] = useState<TokenV3Model[]>([])
  const {
    result,
    refetch: refetchTokenBalances,
    isFetched: isFetchedTokens,
    isFetching: isFetchingTokens,
  } = useQueryResponse({
    initialData: {
      query_result: {
        data: { columns: [], rows: initialData?.tokens ?? [] },
        retrieved_at: `0`,
        id: 0,
      },
    },
    queryId: 'token_balances_for_wallet_across_all_chains',
    params: {
      holder_address: address,
    },
    maxAge: 60,
    refetchInterval,
    enabled: Boolean(enabled && address),
  })

  const {
    data: nativeBalances,
    refetch: refetchNativeBalances,
    isFetched: isFetchedNative,
    isFetching: isFetchingNative,
  } = useQuery({
    initialData: initialData?.natives,
    placeholderData: keepPreviousData,
    queryKey: [address, chains],
    queryFn: async () => {
      if (!address) {
        return null
      }

      return getNativeBalances(address, chains)
    },
    enabled: Boolean(enabled && address),
    refetchInterval,
  })

  const {
    data: tokenRpcBalances,
    refetch: refetchTokenRpcBalances,
    isFetched: isFetchedTokenRpc,
    isFetching: isFetchingTokenRpc,
  } = useQuery({
    initialData: initialData?.natives,
    placeholderData: keepPreviousData,
    queryKey: [address, chains, erc20Tokens],
    queryFn: async () => {
      if (!address || !erc20Tokens) {
        return null
      }

      return getErc20Balances(address, chains, erc20Tokens)
    },
    enabled: Boolean(enabled && address),
    refetchInterval,
  })

  const tokenBalances = useMemo(() => {
    const balances: WalletTokenBalance[] = (result?.data?.rows as WalletTokenBalance[]) || []

    if (!tokenRpcBalances) {
      return balances
    }

    // Create a map of existing balances by token address and chain
    const balancesMap = new Map<string, WalletTokenBalance>()
    balances.forEach((balance) => {
      const key = `${balance.token_address.toLowerCase()}-${balance.chain_id}`
      balancesMap.set(key, balance)
    })

    // Override or add RPC balances
    tokenRpcBalances.forEach((rpcBalance) => {
      const key = `${rpcBalance.token_address.toLowerCase()}-${rpcBalance.chain_id}`
      balancesMap.set(key, rpcBalance)
    })

    return Array.from(balancesMap.values())
  }, [result, tokenRpcBalances])

  const refetchBalances = useCallback(() => {
    refetchNativeBalances()
    refetchTokenBalances()
    refetchTokenRpcBalances()
  }, [refetchNativeBalances, refetchTokenBalances, refetchTokenRpcBalances])

  useEffect(() => {
    const allTokens = [...(nativeBalances ?? []), ...(tokenBalances ?? [])]
    const tokenIds = tokens.map((x) => x.id.toLocaleLowerCase())
    const balancesIds = allTokens.map((x) =>
      `${x.token_address}-${Object.keys(mapGuruNetworkToChainId).find((key) => mapGuruNetworkToChainId[key] === parseInt(x.chain_id))}`.toLocaleLowerCase()
    )

    const tokenIdsDiff = balancesIds.filter((x) => !tokenIds.includes(x))
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
              symbols: ['UNKN', 'UNKN'],
              address,
              network,
              name: 'Unknown Token',
              priceUSD: 0,
              priceUSDChange24h: 0,
            } as TokenV3Model
          }),
        ])
      })
    }
  }, [tokenBalances, nativeBalances, tokens])

  const tokenBalancesWithTokenData: TokenV3ModelWithBalances[] = useMemo(
    () =>
      tokenBalances
        .map((balance) => {
          const token = tokens.find(
            (x) =>
              x.id ===
              `${balance.token_address}-${Object.keys(mapGuruNetworkToChainId).find((key) => mapGuruNetworkToChainId[key] === parseInt(balance.chain_id))}`
          )
          if (token) {
            const tokenWithBalance: TokenV3ModelWithBalances = { ...balance, ...token }
            return tokenWithBalance
          }
        })
        .filter((x) => !!x),
    [tokenBalances, tokens]
  )

  const nativeBalancesWithTokenData: TokenV3ModelWithBalances[] = useMemo(
    () =>
      (nativeBalances || [])
        .map((balance) => {
          const token = tokens.find(
            (x) =>
              x.id ===
              `${balance.token_address}-${Object.keys(mapGuruNetworkToChainId).find((key) => mapGuruNetworkToChainId[key] === parseInt(balance.chain_id))}`
          )
          if (token) {
            const tokenWithBalance: TokenV3ModelWithBalances = {
              ...balance,
              ...token,
            }
            return tokenWithBalance
          }
        })
        .filter((x) => !!x),
    [nativeBalances, tokens]
  )

  return {
    tokens: tokenBalancesWithTokenData,
    natives: nativeBalancesWithTokenData,
    refetch: refetchBalances,
    isFetched: isFetchedTokens || isFetchedNative || isFetchedTokenRpc,
    isFetching: isFetchingTokens || isFetchingNative || isFetchingTokenRpc,
    isFetchingNative,
    isFetchingTokens,
    isFetchingTokenRpc,
  }
}
