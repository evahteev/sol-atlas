import { SolanaAdapter } from '@reown/appkit-adapter-solana/react'
import { AppKitNetwork, solana, solanaDevnet, solanaTestnet } from '@reown/appkit/networks'
import { env } from 'next-runtime-env'

// 0. Set up Solana Adapter
export const solanaWeb3JsAdapter = new SolanaAdapter()

// Your Reown Cloud project ID
export const projectId = `${env('NEXT_PUBLIC_PROJECT_ID')}` // must be NEXT_PUBLIC

export const networks: [AppKitNetwork, ...AppKitNetwork[]] = [solana, solanaTestnet, solanaDevnet]
