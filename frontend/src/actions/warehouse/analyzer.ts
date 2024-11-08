'use server'

import { unstable_cache } from 'next/cache'

import { WarehouseDashboardAnalyzerHistoryEntryProps } from '@/components/feature/WarehouseDashboard/WarehouseDashboardAnalyzer/WarehouseDashboardAnalyzer'

import { appFetch } from './fetch'

type WarehouseDashboardPromptsProps = {
  slug: string
  params?: Record<string, unknown>
  history?: WarehouseDashboardAnalyzerHistoryEntryProps[]
}
export const fetchWarehouseDashboardPrompts = ({
  slug,
  params = {},
  history = [],
}: WarehouseDashboardPromptsProps) =>
  appFetch({
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
export const getWarehouseDashboardPrompts = unstable_cache(
  async (props: WarehouseDashboardPromptsProps): Promise<string[] | null> =>
    (await fetchWarehouseDashboardPrompts(props)
      .then((res) => res.json())
      .catch(() => null)) ?? null,
  ['getWarehouseDashboardPrompts'],
  { revalidate: 3 }
)

type WarehouseDashboardAnalyzeProps = {
  slug: string
  params?: Record<string, unknown>
  prompt?: string | null
}
export const fetchWarehouseDashboardAnalyze = ({
  slug,
  params,
  prompt,
}: WarehouseDashboardAnalyzeProps) =>
  appFetch({
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
export const getWarehouseDashboardAnalyze = unstable_cache(
  async ({ slug, params, prompt }: WarehouseDashboardAnalyzeProps): Promise<string | null> =>
    (
      await fetchWarehouseDashboardAnalyze({
        slug,
        params,
        prompt,
      })
        .then((res) => res.json())
        .catch(() => null)
    )?.output ?? null,
  ['getWarehouseDashboardAnalyze'],
  { revalidate: 3 }
)
