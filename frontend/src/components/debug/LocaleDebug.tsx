'use client'

import { useParams, usePathname } from 'next/navigation'

import { useLocale } from 'next-intl'
import { env } from 'next-runtime-env'

export function LocaleDebug() {
  const locale = useLocale()
  const pathname = usePathname()
  const params = useParams()

  if (process.env.NODE_ENV !== 'development') {
    return null
  }

  return (
    <div
      style={{
        position: 'fixed',
        bottom: 20,
        right: 20,
        background: 'rgba(0, 0, 0, 0.8)',
        color: 'white',
        padding: '10px',
        borderRadius: '5px',
        fontSize: '12px',
        fontFamily: 'monospace',
        zIndex: 9999,
      }}>
      <div>Current Locale: {locale}</div>
      <div>URL Locale: {params.locale || 'none'}</div>
      <div>Pathname: {pathname}</div>
      <div>Default: {env('NEXT_PUBLIC_DEFAULT_LOCALE') || 'en'}</div>
    </div>
  )
}
