'use client'

import { FC, useContext } from 'react'

import QuestList from '@/components/composed/Quest/QuestList'
import { QuestListProps } from '@/components/composed/Quest/QuestList/QuestList'
import { useCheckNFTOwnership } from '@/hooks/useNftBalances'
import { AppContext } from '@/providers/context'

import { getFilter } from './utils'

export const PageQuestsListClient: FC<QuestListProps & { tab?: string }> = ({
  className,
  initialData,
  tab,
}) => {
  const {
    config: { NATIVE_CURRENCY_SYMBOL, pointsToken },
  } = useContext(AppContext)
  const { data: isNFTHolder } = useCheckNFTOwnership()

  return (
    <QuestList
      unit={
        tab === 'mainnet' ? NATIVE_CURRENCY_SYMBOL || 'GURU' : pointsToken.symbols?.[0] || 'POINTS'
      }
      className={className}
      initialData={initialData}
      filter={{ flows: getFilter(tab, isNFTHolder) }}
    />
  )
}
