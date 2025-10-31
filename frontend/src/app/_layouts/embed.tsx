import type { Metadata } from 'next'
import { headers } from 'next/headers'

import { PropsWithChildren } from 'react'

import { env } from 'next-runtime-env'

import styles from '../[locale]/_assets/layout.module.scss'

// Since this is the root layout, all fetch requests in the app
// that don't set their own cache option will be cached.
export const fetchCache = 'default-cache'

export async function generateMetadata(): Promise<Metadata> {
  return {
    title: `${env('NEXT_PUBLIC_APP_NAME')} App – AI-Powered Blockchain Automations and Rewards`,
    description: `Join the ${env('NEXT_PUBLIC_APP_NAME')} on Telegram: Experience AI-powered blockchain automations, create decentralized applications, and earn rewards by participating in the network!`,

    icons: [env('NEXT_PUBLIC_APP_LOGO') || '/favicon.svg'],
    metadataBase: new URL(`https://${(await headers()).get('host')}`),
  }
}

export default async function LayoutEmbed({ children }: PropsWithChildren) {
  return (
    <div className={styles.body} id="page-body">
      <div className={styles.content} id="page-content">
        {children}
      </div>
    </div>
  )
}
