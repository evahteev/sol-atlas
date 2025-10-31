import { CaipAddress } from '@reown/appkit'
import { useQuery } from '@tanstack/react-query'
import { readContract, readContracts } from '@wagmi/core'
import { AssetId, AssetType } from 'caip'
import { useSession } from 'next-auth/react'
import { env } from 'next-runtime-env'
import { Address } from 'viem'

import { wagmiAdapter } from '@/config/wagmi'
import { NFTCollectionBalance, NFTMetadata } from '@/models/nft'

import { communityNftAbi } from './useNftBalances.module'

function truncateCaipNft(caipString: string): CaipAddress {
  return caipString.replace(/\/\d+$/, '') as CaipAddress
}
export async function fetchNFTFromContract(nftContract: CaipAddress, address: string) {
  let ChainIdParams, assetName
  try {
    const assetType = AssetType.parse(nftContract)
    ChainIdParams = assetType.chainId
    assetName = assetType.assetName
  } catch (e) {
    console.error(e)
    const assetId = AssetId.parse(nftContract)

    ChainIdParams = assetId.chainId
    assetName = assetId.assetName
    nftContract = truncateCaipNft(nftContract)
  }
  const chainId =
    typeof ChainIdParams === 'string' ? parseInt(ChainIdParams) : parseInt(ChainIdParams.reference)
  const nftContractAddress = typeof assetName === 'string' ? assetName : assetName.reference

  const collectionName = await readContract(wagmiAdapter.wagmiConfig, {
    address: nftContractAddress as Address,
    abi: communityNftAbi,
    functionName: 'name',
    chainId,
  })

  const nftCollectionBalance: NFTCollectionBalance = {
    caipAddress: nftContract,
    collectionName,
    chainId,
    nftBalance: [],
  }

  const nftBalance = await readContract(wagmiAdapter.wagmiConfig, {
    address: nftContractAddress as Address,
    abi: communityNftAbi,
    functionName: 'balanceOf',
    args: [address as Address],
    chainId,
  })

  const balance = Number(nftBalance)
  if (!balance) {
    return nftCollectionBalance
  }
  try {
    for (let i = 0; i < balance; i++) {
      const tokenId = await readContract(wagmiAdapter.wagmiConfig, {
        address: nftContractAddress as Address,
        abi: communityNftAbi,
        functionName: 'tokenOfOwnerByIndex',
        args: [address as Address, BigInt(i)],
        chainId,
      })

      const tokenURI = await readContract(wagmiAdapter.wagmiConfig, {
        address: nftContractAddress as Address,
        abi: communityNftAbi,
        functionName: 'tokenURI',
        args: [tokenId],
        chainId,
      })

      if (tokenURI) {
        const response = await fetch(tokenURI, {
          cache: 'force-cache',
        })
        const metadata: NFTMetadata = await response.json()

        nftCollectionBalance.nftBalance.push({
          tokenId: Number(tokenId),
          metadata,
        })
      } else {
        nftCollectionBalance.nftBalance.push({
          tokenId: Number(tokenId),
          metadata: {
            description: `NFT #${tokenId}`,
            external_url: '',
            image: '',
            name: `NFT #${tokenId}`,
          },
        })
      }
    }
  } catch (e) {
    console.error(`Error reading nft item data: ${e}`)
  }
  return nftCollectionBalance
}

export async function fetchNFTFromContracts(nftContracts?: CaipAddress[], address?: string) {
  if (!address || !nftContracts?.length) {
    return []
  }

  const results = await Promise.all(
    nftContracts.map((contract) => fetchNFTFromContract(contract, address))
  )

  return results.filter((result) => !!result).flat()
}

export default function useNftBalances({
  contracts,
  address,
  refetchInterval,
}: {
  contracts?: CaipAddress[]
  address?: string | null
  refetchInterval?: number
}) {
  return useQuery({
    queryKey: ['fetchNFTFromContracts', contracts, address],
    queryFn: () => fetchNFTFromContracts(contracts, address as string),
    enabled: !!address && !!contracts?.length, // Only fetch if address and contract are defined
    // staleTime: 1000 * 60 * 5, // 5 minutes cache time
    refetchOnWindowFocus: true,
    refetchInterval,
  })
}

export const checkIfUserHoldsNFT = async (
  nftContracts: CaipAddress[],
  addresses: string[]
): Promise<boolean> => {
  const calls = nftContracts.flatMap((contract) => {
    const { chainId: ChainIdParams, assetName } = AssetType.parse(contract)
    const chainId =
      typeof ChainIdParams === 'string'
        ? parseInt(ChainIdParams)
        : parseInt(ChainIdParams.reference)
    const nftContractAddress = typeof assetName === 'string' ? assetName : assetName.reference

    return addresses.map((address) => ({
      address: nftContractAddress as Address,
      abi: communityNftAbi,
      functionName: 'balanceOf',
      args: [address as Address],
      chainId,
    }))
  })

  // Use multicall to fetch balances
  const results = await readContracts(wagmiAdapter.wagmiConfig, {
    contracts: calls,
  })

  // Check if any balance is greater than 0
  return results.some((balance) => Number(balance.result) > 0)
}

export const useCheckNFTOwnership = () => {
  const NEXT_PUBLIC_APP_COMMUNITY_NFT_ADDRESSES = env('NEXT_PUBLIC_APP_COMMUNITY_NFT_ADDRESSES')
  const communityNftAddresses: CaipAddress[] = NEXT_PUBLIC_APP_COMMUNITY_NFT_ADDRESSES
    ? JSON.parse(NEXT_PUBLIC_APP_COMMUNITY_NFT_ADDRESSES)
    : []
  const { data: session } = useSession()
  const wallets = session?.user?.web3_wallets?.map((x) => x.wallet_address)
  return useQuery({
    queryKey: ['checkIfUserHoldsNFT', communityNftAddresses, wallets],
    queryFn: () => checkIfUserHoldsNFT(communityNftAddresses, wallets ?? []),
    enabled: !!wallets?.length && communityNftAddresses.length > 0, // Only fetch if address and contracts exist
    staleTime: 1000 * 60 * 5, // Cache for 5 minutes
    refetchOnWindowFocus: false,
  })
}
