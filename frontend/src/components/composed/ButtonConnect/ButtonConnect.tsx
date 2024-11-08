'use client'

import { FC, useCallback, useEffect, useState } from 'react'

import { useAppKit } from '@reown/appkit/react'
import { useAccount } from 'wagmi'

import { Button } from '@/components/ui/Button'
import { getShortAddress } from '@/utils/strings'

export const ButtonConnect: FC = () => {
  const { open } = useAppKit()
  const { address } = useAccount()
  const [caption, setCaption] = useState<string | null>(null)

  const handleConnect = useCallback(() => {
    open()
  }, [open])

  useEffect(() => {
    setCaption(address ? getShortAddress(address) : '')
  }, [address])

  return (
    <Button
      isBlock
      size="xl"
      variant="main"
      onClick={handleConnect}
      caption={caption || 'Connect External Wallet'}
      isDisabled={caption === null}
    />
  )
}
