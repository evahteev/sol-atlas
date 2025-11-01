import { getFlowClient } from '@/services/flow/getClient'

export type FlowConfig = {
  label: string // "Frontend Customization config",
  id: number // 1,
  key: string // "frontend_config",
  status: number // 1,
  value: Record<string, string> // {"app_name":"DexGuru","app_title":"Guru Network App – AI-Powered Blockchain Automations and Rewards","app_description":"Join the Guru Network on Telegram: Experience AI-powered blockchain automations, create decentralized applications, and earn rewards by participating in the network!","bot_name":"guru_network_bot","app_url":"https://dex.guru","socials":{"telegram_chat":"https://t.me/gurunetworkchat","telegram_channel":"https://t.me/dexguru","x":"https://x.com/xgurunetwork","discord":"https://discord.com/invite/dPW8fzwzz9","youtube":"https://www.youtube.com/@gurunetwork_ai"}}
}

export async function getConfigByKey({ key }: { key: string }) {
  const client = getFlowClient()
  const params = { path: { key } }
  const { data, error } = await client.GET('/api/config/{key}', {
    params,
    next: {
      revalidate: 10 * 60,
      tags: ['all', 'getConfigByKey'],
    },
  })
  if (error) {
    console.error('Error in getConfigByKey:', error)
    throw new Error('Error fetching config by ID')
  }
  return (data as FlowConfig) ?? null
}
