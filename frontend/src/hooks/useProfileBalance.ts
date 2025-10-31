import { Address, formatUnits } from 'viem'
import { useBalance } from 'wagmi'

import { guruTestnet } from '@/config/wagmi'

export const useProfileBalance = (
  walletAddress?: Address
): { mainnet: string | null; testnet: string | null } => {
  const { data: balanceTestnet } = useBalance({
    address: walletAddress,
    chainId: guruTestnet.id,
    query: { refetchInterval: 60 * 1000 },
  })
  return {
    mainnet: null,
    testnet: balanceTestnet ? formatUnits(balanceTestnet?.value, balanceTestnet?.decimals) : null,
  }
}
