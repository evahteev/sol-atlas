'use client'

import { useSession } from 'next-auth/react'

export const useWalletAddress = () => {
  const { data: session } = useSession()
  const guruWallet = session?.user.web3_wallets.find((x) => x.network_type === 'guru')
  return guruWallet?.wallet_address ?? null
}
