import { env } from 'next-runtime-env'
import { Address } from 'viem'

if (!env('NEXT_PUBLIC_EVM_FEE_WALLET') || !env('NEXT_PUBLIC_SOL_REF_KEY')) {
  throw new Error("ref wallets for swaps aren't defined!")
}

export const SWAP_PROVIDERS = [
  'debridge',
  'guruswap',
  'kyberswap',
  'bridge',
  'paraswap',
  'jupiter',
  'bebop',
] as const
export type SwapProvider = (typeof SWAP_PROVIDERS)[number]
export const disabledProviders = ['jupiter', 'bebop']

export const feeAddressReceiver = `${env('NEXT_PUBLIC_EVM_FEE_WALLET')}`
export const integrator = 'gurunetwork' as const
export const debridgeRefCode = '30625' as const
export const jupiterReferralPubKey = `${env('NEXT_PUBLIC_SOL_REF_KEY')}`
export const solRPC =
  'https://solana-mainnet.core.chainstack.com/b742bfed4719d5b5c6e3efec2bf20331' as const
export const debridgeContainerId = 'debridge-widget-container' as const
export const jupiterContainerId = 'jupiter-widget-container' as const

export const GURU_BASE_ADDRESS = '0x0f1cfd0bb452db90a3bfc0848349463010419ab2'
export const GURU_CHEST_ADDRESS = env('NEXT_PUBLIC_GURU_CHEST_ADDRESS') as Address
