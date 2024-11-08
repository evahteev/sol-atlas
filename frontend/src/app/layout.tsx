import type { Metadata } from 'next'
import { Space_Grotesk } from 'next/font/google'
import { headers } from 'next/headers'

import { PropsWithChildren } from 'react'

import { Flip, ToastContainer } from 'react-toastify'

import { ErrorBoundary } from '@/components/ErrorBoundary'
import ProfileBar from '@/components/composed/ProfileBar'
import { MainMenu } from '@/components/page'
import IconStats from '@/images/icons/stats.svg'
import IconTasks from '@/images/icons/tasks.svg'
// import IconBurn from '@/images/icons/fire.svg'
// import IconAuto from '@/images/icons/auto.svg'
// import IconArena from '@/images/icons/leaderboard.svg'
import IconTokenSwap from '@/images/icons/token_swap.svg'
import IconTokens from '@/images/icons/tokens.svg'
import { AppProvider } from '@/providers'
import Web3ModalProvider from '@/providers/Web3ModalProvider'
import '@/styles/index.scss'

import ErrorPage from './error'

import styles from './_assets/layout.module.scss'

export const metadata: Metadata = {
  title: `${process.env.NEXT_PUBLIC_APP_NAME} App – AI-Powered Blockchain Automations and Rewards`,
  description: `Join the ${process.env.NEXT_PUBLIC_APP_NAME} on Telegram: Experience AI-powered blockchain automations, create decentralized applications, and earn rewards by participating in the network!`,
}

const spaceGrotesk = Space_Grotesk({
  subsets: ['latin', 'latin-ext'],
  variable: '--font-spaceGrotesk',
})

const mainMenuLinks = [
  {
    icon: <IconTasks />,
    href: '/tasks',
    caption: 'Quests',
  },
  {
    icon: <IconStats />,
    href: '/stats',
    caption: 'Stats',
  },
  {
    icon: <IconTokens />,
    href: '/tokens',
    caption: 'Tokens',
  },
  {
    icon: <IconTokenSwap />,
    href: '/swap',
    caption: 'Swap',
  },
]

export default function RootLayout({ children }: PropsWithChildren) {
  const cookies = headers().get('cookie')

  return (
    <html className={spaceGrotesk.variable} lang="en">
      <body>
        <div className={styles.container}>
          <div className={styles.body}>
            <div className={styles.content}>
              <ErrorBoundary fallback={ErrorPage}>
                <Web3ModalProvider cookies={cookies}>
                  <AppProvider>
                    <ProfileBar className={styles.profile} />
                    {children}
                  </AppProvider>
                </Web3ModalProvider>
              </ErrorBoundary>
            </div>
          </div>

          <MainMenu items={mainMenuLinks} className={styles.footer} />
        </div>

        <ToastContainer
          position="top-center"
          closeOnClick
          pauseOnFocusLoss
          pauseOnHover
          theme="dark"
          stacked
          role="alert"
          transition={Flip}
          autoClose={3000}
        />
      </body>
    </html>
  )
}
