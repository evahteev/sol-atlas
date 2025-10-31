import { ChainModel } from '@/models/chain'

export type CustomToken = {
  id: string
  address: string
  name: string
  symbols: string[]
  logoURI: (string | null)[]
  decimals: number
  network: string
  priceUSD?: number
  verified?: boolean
}

export type SwapSummary = {
  chainFrom: ChainModel
  chainTo: ChainModel
  tokenFrom: CustomToken
  tokenTo: CustomToken
  amount: number
}
