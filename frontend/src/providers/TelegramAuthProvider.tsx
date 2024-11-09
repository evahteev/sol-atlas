'use client'

import { useEffect } from 'react'

import { useLaunchParams } from '@telegram-apps/sdk-react'
import { getCsrfToken, signIn, useSession } from 'next-auth/react'

export const TelegramAuthProvider = () => {
  const launchParams = useLaunchParams()

  const { status } = useSession()

  useEffect(() => {
    const handleSignIn = async () => {
      console.log('handleSignIn')
      const csrfToken = await getCsrfToken()
      // console.log('CSRF Token:', csrfToken);

      if (launchParams?.initData?.user && status === 'unauthenticated') {
        signIn('credentials', {
          csrfToken,
          telegram_user: JSON.stringify(launchParams.initData.user),
          redirect: false,
        })
          .then((response) => {
            console.log('Sign-in initiated, response:', response)
            if (response?.error) {
              console.error('Sign-in failed:', response.error)
            }
          })
          .catch((err) => {
            console.error('Sign-in failed:', err)
          })
      }
    }

    if (status === 'unauthenticated') {
      handleSignIn()
    }
  }, [launchParams, status])

  return null
}
