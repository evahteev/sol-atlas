'use client'

import { ReactNode } from 'react'

import { GoogleAnalytics, GoogleTagManager } from '@next/third-parties/google'
import { YandexMetricaProvider } from 'next-yandex-metrica'

import { Show } from '@/components/ui'

const GA_TRACKING_ID = process.env.NEXT_PUBLIC_GA_TRACKING_ID

export default function AnalyticsProvider({ children }: { children: ReactNode }) {
  return (
    <>
      <Show if={GA_TRACKING_ID}>
        <GoogleTagManager gtmId={GA_TRACKING_ID ?? 'G-617E968S0R'} />
        <GoogleAnalytics gaId={GA_TRACKING_ID ?? 'G-617E968S0R'} />
      </Show>

      <YandexMetricaProvider
        tagID={parseInt(process.env.NEXT_PUBLIC_YANDEX_METRICA_ID || '98186048')}
        initParameters={{
          clickmap: true,
          trackLinks: true,
          accurateTrackBounce: true,
        }}>
        {children}
      </YandexMetricaProvider>
    </>
  )
}
