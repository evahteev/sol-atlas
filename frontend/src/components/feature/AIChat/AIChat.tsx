'use client'

import { FC } from 'react'

import { FeatureFlag, useFeatureFlag } from '@/lib/feature-flags'
import { components } from '@/services/flow/schema'

import { AIChatBotAPI } from './AIChatBotAPI'
import { AIChatLegacy } from './AIChatLegacy'

export type AIChatPrompt = {
  label: string
  value: string
}

type AIChatProps = {
  className?: string
  instance?: components['schemas']['ProcessInstanceSchema']
  prompts?: AIChatPrompt[] | null
  entry?: { type: string; id: string } | null
  tasks?: components['schemas']['TaskSchema'][] | null
  onControlTasks?: (tasks?: components['schemas']['TaskSchema'][]) => void
  // New props for bot API mode
  integrationId?: string
}

export const AIChat: FC<AIChatProps> = ({
  className,
  instance,
  prompts,
  entry,
  tasks,
  onControlTasks,
  integrationId = 'luka',
}) => {
  const isBotAPIEnabled = useFeatureFlag(FeatureFlag.BOT_API_CHAT)

  // Feature flag: Use bot API or legacy Camunda
  if (isBotAPIEnabled) {
    // New bot API implementation
    return <AIChatBotAPI className={className} integrationId={integrationId} prompts={prompts} />
  }

  // Legacy Camunda implementation
  if (!instance) {
    throw new Error('AIChat: instance prop is required when BOT_API_CHAT feature flag is disabled')
  }

  return (
    <AIChatLegacy
      className={className}
      instance={instance}
      prompts={prompts}
      entry={entry}
      tasks={tasks}
      onControlTasks={onControlTasks}
    />
  )
}
