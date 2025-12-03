'use client'

import { FC } from 'react'

import { useWindowSize } from 'rooks'

import { CustomToken } from '@/components/composed/TaskForm/custom/swapToken/types'

import { TokenOverviewTokenSwapContent } from './content'

export type TokenOverviewTokenSwapStandaloneProps = {
  className?: string
  token: CustomToken
}

export const TokenOverviewTokenSwapStandalone: FC<TokenOverviewTokenSwapStandaloneProps> = ({
  token,
  className,
}) => {
  const size = useWindowSize()

  if ((size?.innerWidth ?? 0) <= 1100) {
    return null
  }

  return <TokenOverviewTokenSwapContent className={className} token={token} />
}
