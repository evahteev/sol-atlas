import { AssetId, ChainId } from 'caip'

import { SwapProvider } from '@/components/ui/SwapFrame/settings'
import { ChainModel } from '@/models/chain'

export const getChainByName = (chains: ChainModel[], name?: string): ChainModel | null => {
  return chains.find((chain) => chain.name === name) ?? null
}

export const getChainInnerName = (name: string): string => {
  const nameStr = name.toLowerCase()

  switch (nameStr) {
    case 'eth': {
      return 'ethereum'
    }
  }

  return nameStr
}

/**
 * Maps chain IDs and namespaces to OpenSea-supported network names.
 * Supports both EVM and non-EVM chains (e.g., Solana).
 */
const chainIdToNetworkMap: { [key: string]: string } = {
  'eip155:1': 'ethereum', // Ethereum Mainnet
  'eip155:8453': 'base', // Base Mainnet
  'eip155:84532': 'base_sepolia', // Base Mainnet
  solana: 'solana', // Solana
  // Add other supported chains as needed
}

/**
 * Builds an OpenSea URL from a CAIP-19 compliant asset ID.
 *
 * @param {string} assetId - CAIP-19 asset ID (e.g., "eip155:1/erc721:0xab16a96d359ec26a11e2c2b3d8f8b8942d5bfcdb/1").
 * @returns {string} - The OpenSea URL for the specified NFT.
 * @throws {Error} - Throws an error if the chain is unsupported.
 *
 * @example
 * buildOpenSeaUrlFromCAIP("eip155:1/erc721:0xab16a96d359ec26a11e2c2b3d8f8b8942d5bfcdb/1");
 * // Returns: "https://opensea.io/assets/ethereum/0xab16a96d359ec26a11e2c2b3d8f8b8942d5bfcdb/1"
 *
 * @example
 * buildOpenSeaUrlFromCAIP("solana:214gAnKQUfFoD6AW4aRtETJNA73WZ3mYUybMEp3PDqHy");
 * // Returns: "https://opensea.io/assets/solana/214gAnKQUfFoD6AW4aRtETJNA73WZ3mYUybMEp3PDqHy"
 */
export function buildOpenSeaUrlFromCAIP(assetId: string): string {
  const { chainId, assetName, tokenId } = AssetId.parse(assetId)
  const caipChainId = new ChainId(chainId)
  // Map chain ID to OpenSea network name
  const network = chainIdToNetworkMap[caipChainId.toString()]
  if (!network) {
    throw new Error(`Unsupported chain ID or namespace: ${chainId}`)
  }

  // Parse asset details based on CAIP-19 format
  const contractAddress = typeof assetName === 'string' ? assetName : assetName.reference
  const origin = network === 'base_sepolia' ? 'https://testnets.opensea.io' : 'https://opensea.io'
  // Construct the URL based on network type and asset details
  return tokenId
    ? `${origin}/assets/${network}/${contractAddress}/${tokenId}`
    : `${origin}/assets/${network}/${contractAddress}`
}

export const mapGuruNetworkToChainId: Record<string, number> = {
  eth: 1,
  ethsepolia: 11155111,
  optimism: 10,
  bsc: 56,
  polygon: 137,
  sonic: 146,
  arbitrum: 42161,
  avalanche: 43114,
  gnosis: 100,
  canto: 7700,
  nova: 42170,
  zkevm: 1101,
  base: 8453,
  manta: 169,
  graphlinq: 614,
  xfitest: 4157,
  guru: 260,
  matchain: 698,
  solana: 7565164,
  bsc_testnet: 97,
}

export const mapNetwork = (network: string, provider: SwapProvider): string => {
  const mappings: Record<SwapProvider, Record<string, string>> = {
    bebop: {
      eth: 'ethereum',
      arbitrum: 'arbitrum+one',
      base: 'base',
      bsc: 'bnb+chain',
      optimism: 'op+mainnet',
      polygon: 'polygon',
    },
    kyberswap: {
      eth: 'ethereum',
      arbitrum: 'arbitrum',
      base: 'base',
      bsc: 'bnb',
      optimism: 'optimism',
      polygon: 'polygon',
      avalanche: 'avalanche',
    },
    paraswap: {
      eth: 'ethereum',
    },
    debridge: {
      eth: 'ethereum', // Add the appropriate mappings for debridge
      arbitrum: 'arbitrum',
      base: 'base',
      bsc: 'bnb',
      optimism: 'optimism',
      polygon: 'polygon',
      avalanche: 'avalanche',
    },
    jupiter: {
      solana: 'solana',
    },
    guruswap: {},
    bridge: {},
  }

  return mappings[provider]?.[network] ?? network
}
