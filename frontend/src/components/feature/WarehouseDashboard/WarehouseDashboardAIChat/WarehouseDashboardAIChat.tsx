'use client'

import { FC, useContext } from 'react'

import { useDidMount, useWillUnmount } from 'rooks'

import { AIChatPrompt } from '@/components/feature/AIChat/AIChat'
import { AppContext } from '@/providers/context'

export const WarehouseDashboardAIChat: FC<{
  prompts: AIChatPrompt[]
  entry?: { type: string; id: string }
}> = ({ prompts, entry }) => {
  const {
    aiChat: { setPrompts, setEntry },
  } = useContext(AppContext)

  useDidMount(() => {
    setPrompts?.(prompts)
    setEntry?.(entry)
  })

  useWillUnmount(() => {
    setPrompts?.()
    setEntry?.()
  })

  return null
}
