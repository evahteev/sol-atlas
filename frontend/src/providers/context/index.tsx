'use client'

import { usePathname, useRouter, useSearchParams } from 'next/navigation'

import { PropsWithChildren, createContext, useCallback, useEffect, useState } from 'react'

import { getCookie, setCookie } from 'cookies-next/client'
import jwt from 'jsonwebtoken'
import { signOut, useSession } from 'next-auth/react'
import { useActiveWallet, useDisconnect } from 'thirdweb/react'

import { logout } from '@/actions/thirdweb'
import { CustomToken } from '@/components/composed/TaskForm/custom/swapToken/types'
import { AIChatPrompt } from '@/components/feature/AIChat/AIChat'
import { DEFAULT_REDIRECT_PATH, REF_USER_ID_COOKIE_NAME } from '@/config/settings'
import { ApplicationSettings } from '@/framework/config'
import { useTokens } from '@/hooks/tokens/useTokens'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'

type AppContext = {
  config: ApplicationSettings
  chains: ChainModel[]
  aiChat: {
    prompts?: AIChatPrompt[] | null
    setPrompts?: (prompts?: AIChatPrompt[] | null) => void
    entry?: { type: string; id: string } | null
    setEntry?: (entry?: { type: string; id: string }) => void
  }
}
const appContextDefault: AppContext = {
  chains: [],
  config: {
    DEFAULT_DASHBOARD_NAME: '',
    LEADERBOARD_DASHBOARD_NAME: '',
    NATIVE_CURRENCY_SYMBOL: '',
    pointsToken: {} as CustomToken,
  },
  aiChat: {},
}
export const AppContext = createContext<AppContext>(appContextDefault)

export default function AppContextProvider({
  children,
  chains,
  config,
}: PropsWithChildren<{
  chains: ChainModel[]
  config: ApplicationSettings
}>) {
  const { status, data: session } = useSession()

  const pathname = usePathname()
  const router = useRouter()

  const searchParams = useSearchParams()
  const refUserId = searchParams.get('ref')

  const [aiChatPrompts, setAiChatPrompts] = useState<AIChatPrompt[] | null>()
  const [aiChatEntry, setAiChatEntry] = useState<{ type: string; id: string } | null>()
  const [currentChains, setCurrentChains] = useState<ChainModel[]>(chains)

  const { data: nativeTokens } = useTokens(
    { ids: chains.map((chain) => chain.native_token.id) },
    { refetchInterval: 5 * 60 * 1000 }
  )

  const { disconnect } = useDisconnect()
  const wallet = useActiveWallet()
  const handleSignOut = useCallback(async () => {
    if (wallet) {
      disconnect(wallet)
    }
    await logout()
    signOut({ redirectTo: DEFAULT_REDIRECT_PATH })
  }, [disconnect, wallet])

  useEffect(() => {
    const currentRefUserIdCookie = getCookie(REF_USER_ID_COOKIE_NAME)
    if (refUserId && !currentRefUserIdCookie) {
      setCookie(REF_USER_ID_COOKIE_NAME, refUserId, {
        secure: true,
        sameSite: true,
      })
    }
  }, [refUserId])

  useEffect(() => {
    setCurrentChains((prev) =>
      prev.map((chain) => {
        const token = chain.native_token
        const tokenData = (nativeTokens as TokenV3Model[])?.find(
          (token) => token.id === chain.native_token.id
        )
        token.priceUSD = tokenData?.priceUSD
        token.priceUSDChange24h = tokenData?.priceUSDChange24h
        token.verified = true

        return { ...chain, native_token: token }
      })
    )
  }, [nativeTokens])

  useEffect(() => {
    if (
      status === 'authenticated' &&
      session.user?.is_block === true &&
      !pathname.startsWith('/staking') &&
      !pathname.startsWith('/agents')
    ) {
      router.push('/flow/community_onboarding')
    }
  }, [pathname, router, session?.user?.is_block, status])

  useEffect(() => {
    if (session?.access_token) {
      const payloadJWT = jwt.decode(session.access_token)
      if (payloadJWT && Object.prototype.hasOwnProperty.call(payloadJWT, 'exp')) {
        const exp = (payloadJWT as jwt.JwtPayload).exp
        if (exp && new Date(exp * 1000).getTime() < Date.now()) {
          console.warn('thirdweb JWT was expired, signin out')
          handleSignOut()
        }
      }
    }
  }, [handleSignOut, session?.access_token])

  return (
    <AppContext.Provider
      value={{
        chains: currentChains,
        config,
        aiChat: {
          prompts: aiChatPrompts,
          setPrompts: (prompts?: AIChatPrompt[] | null) => setAiChatPrompts(prompts),
          entry: aiChatEntry,
          setEntry: (entry?: { type: string; id: string }) => {
            setAiChatEntry(entry)
          },
        },
      }}>
      {children}
    </AppContext.Provider>
  )
}
