import { useBalance } from 'wagmi'

import { tGuru } from '@/config/wagmi'

import { useWalletAddress } from './useWalletAddress'

export const useBurnsBalance = () => {
  const userAddress = useWalletAddress()
  const { data } = useBalance({
    address: userAddress as `0x${string}`,
    chainId: tGuru.id,
  })
  return data?.formatted ?? null
}
