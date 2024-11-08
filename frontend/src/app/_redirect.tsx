'use client'

import { useRouter } from 'next/navigation'

import { useEffect } from 'react'

import { useLaunchParams } from '@telegram-apps/sdk-react'
import { useSession } from 'next-auth/react'

import { restoreUUID } from '@/hooks/useStartAppParams'

export default function PageIndexRedirect() {
  const launchParams = useLaunchParams()
  const { data: session } = useSession()
  const router = useRouter()

  useEffect(() => {
    if (!launchParams || !session?.user) {
      return
    }

    if (session.user.web3_wallets.length === 0) {
      router.push('/signup')
      return
    }

    if (launchParams?.startParam?.includes('gen')) {
      const shortUUID = launchParams?.startParam.split('gen')[1]
      const uuid = restoreUUID(shortUUID)
      router.push(`/gen/${uuid}`)
      return
    }
    if (launchParams?.startParam?.startsWith('tasks')) {
      router.push('/tasks')
      return
    }
    router.push('/tokens')
  }, [router, launchParams, session])

  return null
}
