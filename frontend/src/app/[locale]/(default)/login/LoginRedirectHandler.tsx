'use client'

import { useRouter } from 'next/navigation'

import { useEffect, useRef, useState } from 'react'

import { useSession } from 'next-auth/react'

import { DEFAULT_REDIRECT_PATH } from '@/config/settings'
import useAuth from '@/hooks/useAuth'

function isValidCallbackUrl(url: string): boolean {
  try {
    // Only allow relative URLs for security
    return url.startsWith('/') && !url.startsWith('//')
  } catch {
    return false
  }
}

export function LoginRedirectHandler() {
  const { isAuth } = useAuth()
  const { data: session } = useSession()
  const router = useRouter()
  const [callbackUrl, setCallbackUrl] = useState<string | null>(null)
  const [isMounted, setIsMounted] = useState(false)
  const hasRedirected = useRef(false)

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

    // Prevent multiple redirects
    if (hasRedirected.current) {
      return // 'Already redirected, skipping')
    }

    // Only redirect if user is authenticated
    if (isAuth) {
      // Mark as redirected to prevent multiple attempts
      hasRedirected.current = true

      // Handle blocked users
      if (session?.user?.is_block) {
        window.location.href = '/agents'
        return
      }

      // Redirect to callback URL or default path
      const targetUrl =
        callbackUrl && isValidCallbackUrl(callbackUrl) ? callbackUrl : DEFAULT_REDIRECT_PATH

      // Use window.location for a hard redirect to ensure middleware sees the session
      window.location.href = targetUrl
    }
  }, [session, router, callbackUrl, isMounted, isAuth])

  return null // This component doesn't render anything
}
