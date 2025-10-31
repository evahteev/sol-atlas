'use client'

import { FC } from 'react'

import { useQuery } from '@tanstack/react-query'

import { fetchTokenProfiles } from '@/actions/tokens'
import TokensMarquee from '@/components/composed/TokensMarquee'
import { ChainModel } from '@/models/chain'

type TokensExplorerTokensMarqueeProps = {
  className?: string
  chains: ChainModel[]
}

export const TokensExplorerTokensMarquee: FC<TokensExplorerTokensMarqueeProps> = ({
  chains,
  className,
}) => {
  const { data } = useQuery({
    queryKey: ['miles_deutscher_portfolio'],
    queryFn: () =>
      fetchTokenProfiles({
        tags: ['miles_deutscher_portfolio'],
        limit: 100,
        offset: 0,
      }).then((res) => res),
  })

  return (
    <TokensMarquee
      id="tokens-marquee"
      className={className}
      chains={chains}
      tokens={
        data?.map((token) => ({
          address: token.token_address,
          network: token.network,
          logoURI: [token.logo_uri ?? ''],
          symbols: [token.symbol ?? ''],
          priceUSDChange24h: token.trending.day.price_move,
        })) ?? []
      }
    />
  )
}
