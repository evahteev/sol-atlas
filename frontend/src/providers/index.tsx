'use client'

import { useRouter } from 'next/navigation'

import { ReactNode, useState } from 'react'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { SessionProvider } from 'next-auth/react'

import { useClientOnce } from '@/hooks/useClientOnce'
import { TelegramAuthProvider } from '@/providers/TelegramAuthProvider'

import { TelegramSetup } from './TelegramSetup'
import AnalyticsProvider from './analytics'

const queryClient = new QueryClient()

export function AppProvider({ children }: { children: ReactNode }) {
  const [isTelegramEnv, setIsTelegramEnv] = useState(false)
  const router = useRouter()
  useClientOnce(() => {
    TelegramSetup(process.env.NODE_ENV !== 'production').then((isTgEnv) => {
      setIsTelegramEnv(isTgEnv)

      if (!isTgEnv) {
        router.push('/tokens')
      }
    })
  })

  return (
    <QueryClientProvider client={queryClient}>
      <ReactQueryDevtools initialIsOpen={false} />
      <SessionProvider>
        {isTelegramEnv && <TelegramAuthProvider />}
        <AnalyticsProvider>{children}</AnalyticsProvider>
      </SessionProvider>
    </QueryClientProvider>
  )
}
