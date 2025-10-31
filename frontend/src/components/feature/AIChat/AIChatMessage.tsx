'use client'

import { FC, HTMLAttributes } from 'react'

import { MessageRole } from '@copilotkit/runtime-client-gql'
import clsx from 'clsx'
import DOMPurify from 'isomorphic-dompurify'
import { marked } from 'marked'

import Text from '@/components/atoms/Text'
import Show from '@/components/ui/Show'
import { components } from '@/services/flow/schema'
import { getDateTime } from '@/utils/dates'

import styles from './AIChatMessage.module.scss'

type CopilotKitMessage = {
  id: string
  role: MessageRole
  content: string
  createdAt?: string
}

type AIChatMessageProps = HTMLAttributes<HTMLDivElement> & {
  className?: string
  entry?: components['schemas']['TaskSchema']
  message?: CopilotKitMessage
}

export const AIChatMessage: FC<AIChatMessageProps> = ({ className, entry, message, ...props }) => {
  // Support both legacy TaskSchema and new CopilotKit message format
  let content: string
  let type: 'question' | 'answer'
  let timestamp: string | undefined

  if (message) {
    // New CopilotKit message format
    content = message.content
    type = message.role === MessageRole.User ? 'question' : 'answer'
    timestamp = message.createdAt ? new Date(message.createdAt).toISOString() : undefined
  } else if (entry) {
    // Legacy TaskSchema format
    content = entry?.description || ''
    type = (entry?.taskDefinitionKey ?? '') === 'human_reply' ? 'question' : 'answer'
    timestamp = entry.created
  } else {
    // Fallback for invalid props
    content = ''
    type = 'answer'
    timestamp = undefined
  }

  const parsedMarkup = marked
    .parse(content, { async: false })
    .replace(
      /<a href="([^"]+)">/gm,
      '<a href="$1" target="_blank" rel="noopener noreferrer">'
    ) as string

  return (
    <div {...props} className={clsx(styles.container, styles[type], className)}>
      <div className={styles.body}>
        <Show if={timestamp}>
          <span className={styles.time}>{getDateTime(timestamp ?? '')}</span>
        </Show>
        <Text
          className={styles.text}
          dangerouslySetInnerHTML={{
            __html: DOMPurify.sanitize(parsedMarkup),
          }}
        />
      </div>
    </div>
  )
}
