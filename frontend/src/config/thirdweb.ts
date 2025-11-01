import { env } from 'next-runtime-env'
import { createThirdwebClient } from 'thirdweb'
import { arbitrum, base, mainnet } from 'thirdweb/chains'
import { ConnectButtonProps, ConnectEmbedProps } from 'thirdweb/react'
import { ecosystemWallet } from 'thirdweb/wallets'

import { THIRDWEB_ECOSYSTEM_ID } from './settings'
import { projectId } from './wagmi'

const thirdwebClientId = `${env('NEXT_PUBLIC_THIRDWEB_CLIENT_ID')}`
if (!thirdwebClientId) {
  // throw new Error('NEXT_PUBLIC_THIRDWEB_CLIENT_ID not defined')
}

const thirdwebBackendWallet = `${env('NEXT_PUBLIC_THIRDWEB_BACKEND_WALLET')}`
if (!thirdwebBackendWallet) {
  // throw new Error('NEXT_PUBLIC_THIRDWEB_BACKEND_WALLET not defined')
}

export const clientId = thirdwebClientId
const secretKey = process.env.THIRDWEB_SECRET_KEY
export const THIRDWEB_ADMIN_ACCOUNT = thirdwebBackendWallet
export const THIRDWEB_AUTH_TOKEN_LS_KEY = `walletToken-${clientId}-${THIRDWEB_ECOSYSTEM_ID}`

export const client = createThirdwebClient(
  secretKey
    ? {
        clientId,
      }
    : {
        clientId,
        secretKey,
      }
)

export const wallets = [
  ecosystemWallet(THIRDWEB_ECOSYSTEM_ID, {
    auth: { mode: 'redirect' },
  }),
]

export const thirdwebConnectBaseConfig: ConnectButtonProps | ConnectEmbedProps = {
  client: client,
  wallets: wallets,
  chains: [mainnet, base, arbitrum],
  walletConnect: { projectId },
  theme: 'dark',
  accountAbstraction: { chain: base, sponsorGas: false },
  supportedTokens: {
    [1]: [
      {
        address: '0x525574C899A7c877a11865339e57376092168258',
        name: 'GURU Token',
        symbol: 'GURU',
        icon: 'https://etherscan.io/token/images/gurunetwork_32.png',
      },
    ],
    [8453]: [
      {
        address: '0x0f1cFD0Bb452DB90a3bFC0848349463010419AB2',
        name: 'GURU Token',
        symbol: 'GURU',
        icon: 'https://basescan.org/token/images/gurunetwork_32.png',
      },
    ],
    [97]: [
      {
        address: '0x5394572712C6EEA31569bC0119993491fF6675DD',
        name: 'UCOIN',
        symbol: 'U',
        icon: 'https://bscscan.com/token/images/u-topia_32.png',
      },
    ],
    [56]: [
      {
        address: '0xe07710cdcD1c9F0FB04bfd013F9854E4552671cE',
        name: 'UCOIN',
        symbol: 'U',
        icon: 'https://bscscan.com/token/images/u-topia_32.png',
      },
    ],
  },
  supportedNFTs: {
    [1]: ['0xbe223020724cc3e2999f5dceda3120484fdbfef7'],
    [8453]: [
      '0x0902372C13ae4AC73efE30AF3911D20F31Bdfe33',
      '0xeb8ae9ed9df8bff58f9d364eef3c4986f4331d1e',
      '0xbb95f4620dae1da317e1ea8a0fa188f271a10f7c',
      '0x519aa00176fAbef84067f3827072E0795D16102e',
    ],
    [84532]: ['0x9f2e9363d83fDd7eA659dFd40b90F24F6b61F539'],
  },
  privacyPolicyUrl: 'https://docs.dex.guru/resources/privacy-policy',
  termsOfServiceUrl: 'https://docs.dex.guru/resources/terms-of-service',
}
