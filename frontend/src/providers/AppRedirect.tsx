'use client'

import { useRouter } from 'next/navigation'

import { ReactNode, useEffect, useState } from 'react'

import { useSession } from 'next-auth/react'

import { DEFAULT_REDIRECT_PATH } from '@/config/settings'

function isValidCallbackUrl(url: string): boolean {
  try {
    // Only allow relative URLs for security
    return url.startsWith('/') && !url.startsWith('//')
  } catch {
    return false
  }
}

export function AppRedirect({ children }: { children?: ReactNode }) {
  const { data: session } = useSession()
  const router = useRouter()
  const [callbackUrl, setCallbackUrl] = useState<string | null>(null)
  const [isMounted, setIsMounted] = useState(false)

  useEffect(() => {
    setIsMounted(true)
    // Get callback URL from current URL on client side only
    if (typeof window !== 'undefined') {
      const params = new URLSearchParams(window.location.search)
      setCallbackUrl(params.get('callbackUrl'))
    }
  }, [])

  useEffect(() => {
    // Only run after component is mounted on client side
    if (!isMounted) return

    console.log(session)
    if (!session?.user) {
      router.push(DEFAULT_REDIRECT_PATH)
      return
    }
    if (session?.user?.is_block) {
      router.push('/flow/community_onboarding')
      return
    }

    // Check for callbackUrl parameter
    const targetUrl =
      callbackUrl && isValidCallbackUrl(callbackUrl) ? callbackUrl : DEFAULT_REDIRECT_PATH

    router.push(targetUrl)
  }, [router, session, callbackUrl, isMounted])

  // Don't render anything until mounted on client side
  if (!isMounted) {
    return children
  }

  return children
}
