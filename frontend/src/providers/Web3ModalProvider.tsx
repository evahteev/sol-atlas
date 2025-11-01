'use client'

import React, { ReactNode } from 'react'

import { AutoConnect, ThirdwebProvider } from 'thirdweb/react'
import { Config, WagmiProvider, cookieToInitialState } from 'wagmi'

import { thirdwebConnectBaseConfig } from '@/config/thirdweb'
import { wagmiAdapter } from '@/config/wagmi'
import { useConnectHandler } from '@/hooks/useConnectHandler'

import ReownAppKitProvider from './ReownAppkitProvider'

export default function Web3ModalProvider({
  children,
  cookies,
}: {
  children: ReactNode
  cookies: string | null
}) {
  let initialState
  if (cookies) {
    try {
      initialState = cookieToInitialState(wagmiAdapter.wagmiConfig as Config, cookies)
    } catch (e) {
      console.error(`cookieToInitialState error: ${e}`)
    }
  }
  const { onConnectHandler } = useConnectHandler()
  return (
    <ThirdwebProvider>
      <AutoConnect {...thirdwebConnectBaseConfig} onConnect={onConnectHandler} timeout={10000} />

      <WagmiProvider config={wagmiAdapter.wagmiConfig as Config} initialState={initialState}>
        <ReownAppKitProvider>{children}</ReownAppKitProvider>
      </WagmiProvider>
    </ThirdwebProvider>
  )
}
