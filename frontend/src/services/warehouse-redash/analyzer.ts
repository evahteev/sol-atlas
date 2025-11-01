'use server'

import { WarehouseDashboardAnalyzerHistoryEntryProps } from '@/components/feature/WarehouseDashboard/WarehouseDashboardAnalyzer/types'

import { appFetch } from './fetch'

type WarehouseDashboardPromptsProps = {
  slug: string
  params?: Record<string, unknown>
  history?: WarehouseDashboardAnalyzerHistoryEntryProps[]
}
export async function fetchWarehouseDashboardPrompts({
  slug,
  params = {},
  history = [],
}: WarehouseDashboardPromptsProps) {
  return appFetch({
    url: `${process.env.LANGCHAIN_API_URL}/prompts/`,
    method: 'POST',
    data: {
      dashboard_slug: slug,
      parameters: JSON.stringify(params),
      chat_logs: JSON.stringify(history),
    },
    headers: {
      'Content-Type': 'application/json',
      accept: 'application/json',
      session: `${process.env.LANGCHAIN_API_KEY}`,
    },
  })
}
export async function getWarehouseDashboardPrompts(
  props: WarehouseDashboardPromptsProps
): Promise<string[] | null> {
  return (
    (await fetchWarehouseDashboardPrompts(props)
      .then((res) => res.json())
      .catch(() => null)) ?? null
  )
}

type WarehouseDashboardAnalyzeProps = {
  slug: string
  params?: Record<string, unknown>
  prompt?: string | null
}
export async function fetchWarehouseDashboardAnalyze({
  slug,
  params,
  prompt,
}: WarehouseDashboardAnalyzeProps) {
  return appFetch({
    url: `${process.env.LANGCHAIN_API_URL}/endpoints.dashboard_analyze_chain.sequential_chain/run`,
    method: 'POST',
    data: {
      dashboard_slug: slug,
      parameters: params ?? {},
      selected_prompt: prompt,
      prompt_suffix: '',
    },
    headers: {
      'Content-Type': 'application/json',
      accept: 'application/json',
      session: `${process.env.LANGCHAIN_API_KEY}`,
    },
  })
}
export async function getWarehouseDashboardAnalyze({
  slug,
  params,
  prompt,
}: WarehouseDashboardAnalyzeProps): Promise<string | null> {
  return (
    (
      await fetchWarehouseDashboardAnalyze({
        slug,
        params,
        prompt,
      })
        .then((res) => res.json())
        .catch(() => null)
    )?.output ?? null
  )
}
