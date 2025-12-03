'use client'

import { PropsWithChildren, useEffect } from 'react'

import { useAppKitAccount } from '@reown/appkit/react'

import { createReownAppKit } from '@/config/reown'
import { useSession } from '@/hooks/useAuth.compat'
import { WalletType } from '@/hooks/useWalletAddress'
import { FlowClientObject } from '@/services/flow'

createReownAppKit()

export default function ReownAppKitProvider({ children }: PropsWithChildren) {
  const { address } = useAppKitAccount()
  const { data: session, update } = useSession()
  useEffect(() => {
    if (!address || !session?.user?.web3_wallets?.length) {
      return
    }
    const externalWallets = session.user.web3_wallets.filter(
      (x) => x.network_type === WalletType.solana
    )
    if (externalWallets?.some((x) => x.wallet_address?.toLowerCase() === address?.toLowerCase())) {
      return
    }

    if (!session?.user?.webapp_user_id) {
      return
    }
    FlowClientObject.user.update({
      webapp_user_id: session?.user?.webapp_user_id,
      wallet_address: address,
      network_type: WalletType.solana,
    })
    const newSessionUser = { ...session.user }
    newSessionUser.web3_wallets?.push({
      id: `temp_${Date.now()}`, // Temporary ID until Flow API returns the real one
      address: address,
      wallet_address: address,
      network_type: WalletType.solana,
    })
    update({ user: newSessionUser })
  }, [address, session?.user, session?.user?.web3_wallets, session?.user?.webapp_user_id, update])
  return children
}
