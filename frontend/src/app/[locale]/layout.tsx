import type { Metadata } from 'next'
import { Space_Grotesk } from 'next/font/google'
import { headers } from 'next/headers'

import React, { PropsWithChildren } from 'react'

import clsx from 'clsx'
import { SessionProvider } from 'next-auth/react'
import { NextIntlClientProvider } from 'next-intl'
import { getMessages, getTranslations } from 'next-intl/server'
import { PublicEnvScript, env } from 'next-runtime-env'
import { Flip, ToastContainer } from 'react-toastify'

import { fetchChainList } from '@/actions/tokens'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ApplicationSettings } from '@/framework/config'
import AppProvider from '@/providers'
import Web3ModalProvider from '@/providers/Web3ModalProvider'
import AnalyticsProvider from '@/providers/analytics'
import '@/styles/index.scss'

import TooltipProvider from './_components/tooltip/tooltip'
import ErrorPage from './error'

import styles from './_assets/layout.module.scss'

// Since this is the root layout, all fetch requests in the app
// that don't set their own cache option will be cached.
export const fetchCache = 'default-cache'

const config = (await import(`@/framework/${process.env.NEXT_PUBLIC_CI_PROJECT_NAME}/config`))
  .ApplicationSettings as ApplicationSettings

const colorTheme = process.env.COLOR_THEME

function parseCssVarsToStyle(themeString: string): React.CSSProperties {
  const styles: Record<string, string> = {}

  themeString.split(';').forEach((declaration) => {
    const [property, value] = declaration.split(':')
    if (!property || !value) return

    // Convert --color-primary to '--color-primary' as valid key
    styles[property.trim()] = value.trim()
  })

  return styles
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ locale: string }>
}): Promise<Metadata> {
  const { locale } = await params
  const t = await getTranslations({ locale, namespace: 'Metadata' })
  const appName = env('NEXT_PUBLIC_APP_NAME') || 'Axioma 24'

  return {
    title: t('defaultTitle', { appName }),
    description: t('defaultDescription', { appName }),
    keywords: t('keywords'),
    icons: [env('NEXT_PUBLIC_APP_LOGO') || '/favicon.svg'],
    metadataBase: new URL(`https://${(await headers()).get('host')}`),
    openGraph: {
      title: t('siteTitle', { appName }),
      description: t('siteDescription', { appName }),
      type: 'website',
      locale,
      alternateLocale: locale === 'en' ? 'ru' : 'en',
    },
    twitter: {
      card: 'summary_large_image',
      title: t('siteTitle', { appName }),
      description: t('siteDescription', { appName }),
    },
    alternates: {
      languages: {
        en: '/en',
        ru: '/ru',
      },
    },
  }
}

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin', 'latin-ext'],
  variable: '--font-spaceGrotesk',
})

export default async function LayoutRoot({
  children,
  params,
}: PropsWithChildren<{
  params: Promise<{ locale: string }>
}>) {
  const { locale } = await params

  const headersObj = await headers()
  const cookieHeaders = headersObj.get('cookie')
  const chains = await fetchChainList().then((res) => res ?? [])
  const style = colorTheme ? parseCssVarsToStyle(colorTheme) : undefined
  const messages = await getMessages()

  return (
    <html
      className={clsx(spaceGrotesk.variable, env('NEXT_PUBLIC_APP_DESIGN'))}
      lang={locale}
      style={style}
      data-version={process.env.NEXT_PUBLIC_GIT_COMMIT}>
      <AnalyticsProvider />
      <head>
        <PublicEnvScript />
      </head>
      <body>
        <NextIntlClientProvider messages={messages}>
          <SessionProvider>
            <ErrorBoundary fallback={ErrorPage}>
              <Web3ModalProvider cookies={cookieHeaders}>
                <AppProvider chains={chains} config={config}>
                  <div className={styles.container}>{children}</div>
                </AppProvider>
              </Web3ModalProvider>
            </ErrorBoundary>

            <ToastContainer
              position="top-right"
              closeOnClick
              pauseOnFocusLoss
              pauseOnHover
              theme="dark"
              stacked
              role="alert"
              transition={Flip}
              autoClose={3000}
            />
            <TooltipProvider />
          </SessionProvider>
        </NextIntlClientProvider>
      </body>
    </html>
  )
}
