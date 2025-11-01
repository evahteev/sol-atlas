import { WagmiAdapter } from '@reown/appkit-adapter-wagmi'
import {
  AppKitNetwork,
  arbitrum,
  avalanche,
  base,
  baseSepolia,
  bsc,
  canto,
  defineChain,
  gnosis,
  guruTestnet as guruBaseSepolia,
  mainnet,
  manta,
  optimism,
  polygon,
  polygonZkEvm,
  sepolia,
  sonic,
} from '@reown/appkit/networks'
import { env } from 'next-runtime-env'
import { cookieStorage, createStorage, http } from 'wagmi'

export const guruTestnet = {
  ...guruBaseSepolia,
  id: 263,
  blockExplorers: {
    default: {
      name: 'Guruscan',
      url: 'https://explorer-guru-network-qaz67659rw.t.conduit.xyz',
    },
  },
  rpcUrls: {
    default: {
      http: ['https://rpc-test.gurunetwork.ai'],
    },
  },
}

const customChain =
  process.env.APP_CHAIN_ID &&
  process.env.APP_CHAIN_LABEL &&
  process.env.APP_NATIVE_TOKEN_DECIMALS &&
  process.env.APP_NATIVE_TOKEN_NAME &&
  process.env.APP_NATIVE_TOKEN_SYMBOL &&
  process.env.APP_RPC_URL &&
  process.env.APP_BLOCK_EXPLORER_URL
    ? defineChain({
        id: parseInt(process.env.APP_CHAIN_ID),
        caipNetworkId: `eip155:${process.env.APP_CHAIN_ID}`,
        chainNamespace: 'eip155',
        name: process.env.APP_CHAIN_LABEL,
        nativeCurrency: {
          decimals: parseInt(process.env.APP_NATIVE_TOKEN_DECIMALS),
          name: process.env.APP_NATIVE_TOKEN_NAME,
          symbol: process.env.APP_NATIVE_TOKEN_SYMBOL,
        },
        rpcUrls: {
          default: {
            http: [process.env.APP_RPC_URL],
          },
        },
        blockExplorers: {
          default: { name: 'Explorer', url: process.env.APP_BLOCK_EXPLORER_URL },
        },
      })
    : undefined

// Your Reown Cloud project ID
export const projectId = `${env('NEXT_PUBLIC_PROJECT_ID')}` // must be NEXT_PUBLIC

export const networks: [AppKitNetwork, ...AppKitNetwork[]] = [
  arbitrum,
  avalanche,
  base,
  baseSepolia,
  bsc,
  canto,
  gnosis,
  guruTestnet,
  mainnet,
  manta,
  optimism,
  polygon,
  polygonZkEvm,
  sonic,
  sepolia,
]

// add if not duplicate
if (customChain && networks.some((x) => x.id !== customChain.id)) {
  networks.push(customChain)
}

export const wagmiAdapter = new WagmiAdapter({
  networks,
  projectId,
  ssr: true,
  storage: createStorage({
    storage: cookieStorage,
  }),
  transports: {
    [sepolia.id]: http('https://ethereum-sepolia-rpc.publicnode.com'),
    [mainnet.id]: http('https://eth.llamarpc.com'),
    [baseSepolia.id]: http('https://base-sepolia.drpc.org'),
    [guruTestnet.id]: http('https://rpc-test.gurunetwork.ai'),
    [sonic.id]: http(sonic.rpcUrls.default.http[0]),
  },
})
