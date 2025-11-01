import { useSession } from 'next-auth/react'
import { useActiveAccount, useAutoConnect } from 'thirdweb/react'

import { thirdwebConnectBaseConfig } from '@/config/thirdweb'

import { useConnectHandler } from './useConnectHandler'

type AuthData = {
  isAuth: boolean
  isLoading: boolean
}
export default function useAuth(): AuthData {
  const { status } = useSession()
  const account = useActiveAccount()
  const { onConnectHandler } = useConnectHandler()
  useAutoConnect({
    ...thirdwebConnectBaseConfig,
    onConnect: onConnectHandler,
    timeout: 10000,
  })
  const isLoading =
    (status !== 'authenticated' && !!account) || (status === 'authenticated' && !account)
  const isAuth = status === 'authenticated' && !!account
  return {
    isAuth,
    isLoading,
  }
}
