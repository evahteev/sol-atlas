import { CaipAddress } from '@reown/appkit'

export type NFTMetadata = {
  description: string
  external_url: string
  image: string
  name: string
}

export type NFTDetail = {
  tokenId: number
  metadata: NFTMetadata
}

export type NFTCollectionBalance = {
  collectionName: string
  caipAddress: CaipAddress
  chainId?: number
  nftBalance: NFTDetail[]
}
