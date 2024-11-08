'use client'

import { ReactNode, createContext, useState } from 'react'

import { WarehouseDashboardAnalyzerHistoryEntryProps } from './WarehouseDashboardAnalyzer'

export const WarehouseDashboardAnalyzerHistory = createContext<{
  history: WarehouseDashboardAnalyzerHistoryEntryProps[]
  updateHistory: (entry: WarehouseDashboardAnalyzerHistoryEntryProps) => void
  prompts: string[] | null
  updatePrompts: (entry: string[]) => void
}>({
  history: [],
  updateHistory: () => {},
  prompts: null,
  updatePrompts: () => {},
})

export default function WarehouseDashboardAnalyzerHistoryProvider({
  children,
}: {
  children: ReactNode
}) {
  const [history, setHistory] = useState<WarehouseDashboardAnalyzerHistoryEntryProps[]>([])
  const [prompts, setPrompts] = useState<string[]>([])

  return (
    <WarehouseDashboardAnalyzerHistory.Provider
      value={{
        history,
        prompts,
        updateHistory: (entry) =>
          setHistory((prev) => {
            return [...prev, entry]
          }),
        updatePrompts: setPrompts,
      }}>
      {children}
    </WarehouseDashboardAnalyzerHistory.Provider>
  )
}
