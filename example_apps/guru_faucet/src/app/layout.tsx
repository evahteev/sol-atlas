import type { Metadata } from 'next'
import { JetBrains_Mono } from 'next/font/google'
import { headers } from 'next/headers'

import { SessionProvider } from 'next-auth/react'
import { cookieToInitialState } from 'wagmi'

import Web3ModalProvider from '@/components/Web3ModalProvider'
import { config } from '@/config/wagmi'
import { DexguruPageProvider } from '@/providers/page'
import WalletConnectedProvider from '@/providers/wallet'
import '@/styles/index.scss'

const font = JetBrains_Mono({
  subsets: ['latin', 'latin-ext', 'cyrillic', 'cyrillic-ext'],
})

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: 'DexGuru App',
    description: '',
    icons: ['/favicon.svg'],
    metadataBase: new URL(`https://${headers().get('host')}`),
  }
}

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const initialState = cookieToInitialState(config, headers().get('cookie'))

  return (
    <html lang="en" data-version={process.env.GIT_COMMIT}>
      <body className={font.className}>
        <Web3ModalProvider initialState={initialState}>
          <DexguruPageProvider>
            <WalletConnectedProvider>
              <SessionProvider>{children}</SessionProvider>
            </WalletConnectedProvider>
          </DexguruPageProvider>
        </Web3ModalProvider>
      </body>
    </html>
  )
}
