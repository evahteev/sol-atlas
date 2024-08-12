import { defaultWagmiConfig } from '@web3modal/wagmi/react/config'
import { defineChain } from 'viem'
import { cookieStorage, createStorage } from 'wagmi'
import { base, mainnet } from 'wagmi/chains'

import { WALLET_CONNECT_PROJECT_ID } from './settings'

// Get projectId at https://cloud.walletconnect.com
export const projectId = WALLET_CONNECT_PROJECT_ID || ''

if (!projectId) throw new Error('Project ID is not defined')

const metadata = {
  name: 'Connect Wallet',
  description: 'Connect your wallet to get access to more features',
  url: 'https://app.web3auto.guru', // origin must match your domain & subdomain
  icons: ['/favicon.svg'],
}

export const tGuru = defineChain({
  id: 261,
  name: 'Guru Network Testnet',
  nativeCurrency: {
    decimals: 18,
    name: 'testGURU',
    symbol: 'tGURU',
  },
  rpcUrls: {
    default: {
      http: ['https://rpc.gurunetwork.ai/archive/261'],
    },
  },
  blockExplorers: {
    default: { name: 'Explorer', url: 'https://scan.gurunetwork.ai' },
  },
})

export const supportedChains = [tGuru, base, mainnet]

export const config = defaultWagmiConfig({
  // @ts-expect-error TODO: check this attr
  chains: supportedChains,
  projectId,
  metadata,
  ssr: true,
  storage: createStorage({
    storage: cookieStorage,
  }),
  auth: {
    email: true,
    // socials: ['google', 'x', 'github', 'discord'],
  },
})
