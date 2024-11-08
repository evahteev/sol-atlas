'use client'

import React, { ReactNode } from 'react'

import { base, mainnet } from '@reown/appkit/networks'
import { createAppKit } from '@reown/appkit/react'
import { Config, WagmiProvider, cookieToInitialState } from 'wagmi'

import { siweConfig } from '@/config/siwe'
import { projectId, tGuru, wagmiAdapter } from '@/config/wagmi'

// Setup queryClient

if (!projectId) throw new Error('Project ID is not defined')

// Create a metadata object
const metadata = {
  name: 'guru_network_app',
  description: `${process.env.NEXT_PUBLIC_APP_NAME} App`,
  url: 'https://app.gurunetwork.ai', // origin must match your domain & subdomain
  icons: ['https://assets.reown.com/reown-profile-pic.png'],
}

// Create the modal
createAppKit({
  adapters: [wagmiAdapter],
  projectId,
  networks: [mainnet, tGuru, base],
  defaultNetwork: mainnet,
  metadata: metadata,
  features: {
    email: false, // default to true
    socials: [],
    emailShowWallets: true, // default to true
    analytics: true, // Optional - defaults to your Cloud configuration
  },
  siweConfig: siweConfig,
})

export default function Web3ModalProvider({
  children,
  cookies,
}: {
  children: ReactNode
  cookies: string | null
}) {
  const initialState = cookieToInitialState(wagmiAdapter.wagmiConfig as Config, cookies)
  return (
    <WagmiProvider config={wagmiAdapter.wagmiConfig as Config} initialState={initialState}>
      {children}
    </WagmiProvider>
  )
}
