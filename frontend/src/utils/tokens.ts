import { ChainModel } from '@/models/chain'
import { TokenV3ModelWithBalances } from '@/models/token'

import { getAsArray, removeUnprintable } from '.'
import { getChainByName } from './chains'

export const getTokenSymbolsString = (symbols: string | string[]) => {
  const symbolsArr = getAsArray(symbols) ?? []
  return symbolsArr?.map(removeUnprintable).join('/') ?? ''
}

export const getTokenPriceChannel = (
  ticker: string,
  resolution: number,
  chains: ChainModel[]
): string => {
  const [tokenAddress, apendix] = ticker.split('-')
  const [network] = apendix.split('_')
  const currencyCode = 'S' // currency === "USD" ? "S" : "N";
  const chainId = getChainByName(chains, network)?.id

  // expected RoundedCandle.id-S-600-1-all-0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2
  return `RoundedCandle.id-${currencyCode}-${resolution}-${
    chainId || 'unknown'
  }-all-${tokenAddress}`
}

export const getTokenId = ({ address, network }: { address: string; network: string }): string =>
  `${address.toLowerCase()}-${network.toLowerCase()}`

export const isTokenId = (val: string) => /0x[0-9a-f]{40}-[a-z]+/.test(val)

export const getBalanceFromList = (
  balances: TokenV3ModelWithBalances[],
  token?: { id: string; token_address?: string; address?: string; network: string }
) => {
  return (
    balances.find((item) => item.id?.toLocaleLowerCase() === token?.id?.toLocaleLowerCase())
      ?.balance || 0
  )
}
