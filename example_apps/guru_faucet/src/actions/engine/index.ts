'use server'

import { unstable_cache } from 'next/cache'

import { DefinitionModel } from '@/models/definition'
import FlowClient from '@/services/flow/client'

export const getProcessDefinition = unstable_cache(
  async ({
    flowKey,
    isServer = true,
  }: {
    flowKey: string
    isServer?: boolean
  }): Promise<DefinitionModel | null> => {
    const flowClient = new FlowClient({ isServer })

    const definitions = await flowClient.getProcessDefinition(flowKey)
    const definition = definitions?.find((definition) => definition.key === flowKey)

    return definition ?? null
  },
  ['getProcessDefinitionByKey', 'getProcessDefinition'],
  { revalidate: 10 * 60 }
)
