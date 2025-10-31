'use client'

import { PropsWithChildren } from 'react'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'

import { ApplicationSettings } from '@/framework/config'
import { ChainModel } from '@/models/chain'

import AppContextProvider from './context'

const queryClient = new QueryClient()

export default function AppProvider({
  children,
  chains,
  config,
}: PropsWithChildren<{
  chains: ChainModel[]
  config: ApplicationSettings
}>) {
  return (
    <QueryClientProvider client={queryClient}>
      <ReactQueryDevtools initialIsOpen={true} />

      <AppContextProvider chains={chains} config={config}>
        {children}
      </AppContextProvider>
    </QueryClientProvider>
  )
}
