import { WagmiAdapter } from '@reown/appkit-adapter-wagmi'
import { base, defineChain, mainnet } from '@reown/appkit/networks'
import { cookieStorage, createStorage, http } from 'wagmi'

if (!process.env.NEXT_PUBLIC_APP_CHAIN_ID) {
  throw new Error('env var NEXT_PUBLIC_APP_CHAIN_ID is not defined!')
}

if (!process.env.NEXT_PUBLIC_APP_CHAIN_LABEL) {
  throw new Error('env var NEXT_PUBLIC_APP_CHAIN_LABEL is not defined!')
}

if (!process.env.NEXT_PUBLIC_APP_NATIVE_TOKEN_DECIMALS) {
  throw new Error('env var NEXT_PUBLIC_APP_NATIVE_TOKEN_DECIMALS is not defined!')
}

if (!process.env.NEXT_PUBLIC_APP_NATIVE_TOKEN_NAME) {
  throw new Error('env var NEXT_PUBLIC_APP_NATIVE_TOKEN_NAME is not defined!')
}

if (!process.env.NEXT_PUBLIC_APP_NATIVE_TOKEN_SYMBOL) {
  throw new Error('env var NEXT_PUBLIC_APP_NATIVE_TOKEN_SYMBOL is not defined!')
}

if (!process.env.NEXT_PUBLIC_APP_BLOCK_EXPLORER_URL) {
  throw new Error('env var NEXT_PUBLIC_APP_BLOCK_EXPLORER_URL is not defined!')
}

if (!process.env.NEXT_PUBLIC_APP_RPC_URL) {
  throw new Error('env var NEXT_PUBLIC_APP_RPC_URL is not defined!')
}

if (!process.env.NEXT_PUBLIC_APP_CHAIN_LABEL) {
  throw new Error('env var NEXT_PUBLIC_APP_CHAIN_LABEL is not defined!')
}

if (!process.env.NEXT_PUBLIC_PROJECT_ID) {
  throw new Error('env var NEXT_PUBLIC_PROJECT_ID is not defined!')
}

export const tGuru = defineChain({
  id: parseInt(process.env.NEXT_PUBLIC_APP_CHAIN_ID),
  caipNetworkId: `eip155:${process.env.NEXT_PUBLIC_APP_CHAIN_ID}`,
  chainNamespace: 'eip155',
  name: process.env.NEXT_PUBLIC_APP_CHAIN_LABEL,
  nativeCurrency: {
    decimals: parseInt(process.env.NEXT_PUBLIC_APP_NATIVE_TOKEN_DECIMALS),
    name: process.env.NEXT_PUBLIC_APP_NATIVE_TOKEN_NAME,
    symbol: process.env.NEXT_PUBLIC_APP_NATIVE_TOKEN_SYMBOL,
  },
  rpcUrls: {
    default: {
      http: [process.env.NEXT_PUBLIC_APP_RPC_URL],
    },
  },
  blockExplorers: {
    default: { name: 'Explorer', url: process.env.NEXT_PUBLIC_APP_BLOCK_EXPLORER_URL },
  },
})

// Your Reown Cloud project ID
export const projectId = process.env.NEXT_PUBLIC_PROJECT_ID

if (!projectId) {
  throw new Error('Project ID is not defined')
}

export const wagmiAdapter = new WagmiAdapter({
  networks: [mainnet, tGuru, base],
  projectId,
  ssr: true,
  storage: createStorage({
    storage: cookieStorage,
  }),
  transports: {
    [tGuru.id]: http(),
  },
})
