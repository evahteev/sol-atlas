'use client'

import { ReactNode } from 'react'

import clsx from 'clsx'

import Loader from '@/components/atoms/Loader'
import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'
import Show from '@/components/ui/Show'

import styles from './QuestStatus.module.scss'

type QuestStatusProps = {
  message?: ReactNode
  className?: string
  isLoading?: boolean
}

export function QuestStatus({ message, className, isLoading }: QuestStatusProps) {
  if (!message) {
    return null
  }

  return (
    <Card className={clsx(styles.container, className)}>
      <Caption size="xs" className={styles.subtitle}>
        {message ?? 'No message available'}
      </Caption>
      <Show if={isLoading}>
        <Loader className={styles.loader} />
      </Show>
    </Card>
  )
}
