'use client'

import dynamic from 'next/dynamic'

import { FC } from 'react'

import Loader from '@/components/atoms/Loader'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'

const FinancialChart = dynamic(() => import('@/components/feature/FinancialChart'), {
  loading: () => <Loader />,
  ssr: false,
})

type PageTokenChart = {
  token: TokenV3Model
  chains: ChainModel[]
  className?: string
}

export const PageTokenChart: FC<PageTokenChart> = ({ token, chains, className }) => {
  return <FinancialChart className={className} token={token} chains={chains ?? []} />
}
