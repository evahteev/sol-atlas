import { base } from '@reown/appkit/networks'
import { createAppKit } from '@reown/appkit/react'
import { env } from 'next-runtime-env'

import { networks, projectId, solanaWeb3JsAdapter } from './solana'

if (!projectId) {
  throw new Error('Project ID is not defined')
}

// Create a metadata object
const metadata = {
  name: `${env('NEXT_PUBLIC_APP_NAME')}`,
  description: `${env('NEXT_PUBLIC_APP_NAME')} App`,
  url: typeof window !== 'undefined' ? window.location.origin : '', // origin must match your domain & subdomain
  icons: [`${typeof window !== 'undefined' && window.location.origin}/favicon.svg`],
}

export function createReownAppKit() {
  // Create the modal
  return createAppKit({
    adapters: [solanaWeb3JsAdapter],
    projectId,
    networks,
    defaultNetwork: base,
    metadata: metadata,
    features: {
      email: false, // default to true
      swaps: false,
      onramp: false,
      socials: false,
      emailShowWallets: true, // default to true
      analytics: true, // Optional - defaults to your Cloud configuration
    },
    // siweConfig,
  })
}
