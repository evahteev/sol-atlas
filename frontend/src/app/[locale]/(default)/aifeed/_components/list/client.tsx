'use client'

import { FC, useContext } from 'react'

import QuestList from '@/components/composed/Quest/QuestList'
import { QuestListProps } from '@/components/composed/Quest/QuestList/QuestList'
import { AppContext } from '@/providers/context'
import { getTokenSymbolsString } from '@/utils/tokens'

import { getFilter } from './utils'

export const PageAdminListClient: FC<QuestListProps & { tab?: string }> = ({
  className,
  initialData,
  tab,
}) => {
  const {
    config: { NATIVE_CURRENCY_SYMBOL, pointsToken },
  } = useContext(AppContext)
  return (
    <QuestList
      unit={tab === 'mainnet' ? NATIVE_CURRENCY_SYMBOL : getTokenSymbolsString(pointsToken.symbols)}
      className={className}
      initialData={initialData}
      filter={{ flows: getFilter() }}
    />
  )
}
