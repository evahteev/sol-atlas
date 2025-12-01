'use client'

import { useSession } from '@/hooks/useAuth.compat'

export enum WalletType {
  'guru' = 'guru',
  'thirdweb_ecosystem' = 'thirdweb_ecosystem',
  'solana' = 'solana',
}

export const useWalletAddress = (type: WalletType): string | null => {
  const { data: session } = useSession()
  const guruWallet = session?.user?.web3_wallets?.find((x) => x.network_type === type)
  return guruWallet?.wallet_address ?? null
}
