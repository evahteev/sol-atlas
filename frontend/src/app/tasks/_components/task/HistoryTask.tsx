import { FC } from 'react'

import clsx from 'clsx'

import { Caption, Card, Show } from '@/components/ui'
import IconDone from '@/images/icons/success.svg'

import styles from './Task.module.scss'

export const HistoryTask: FC<{ title: string; description?: string | null }> = ({
  title,
  description,
}) => {
  return (
    <>
      <Card className={clsx(styles.container, styles.completed)}>
        <div className={styles.body}>
          <Caption variant="body" size="sm" strong className={styles.title}>
            {title}
          </Caption>
          <Show if={description}>
            <Caption size="xs" className={styles.subtitle}>
              {description}
            </Caption>
          </Show>
        </div>
        <div className={styles.footer}>
          <IconDone className={styles.icon} />
        </div>
      </Card>
    </>
  )
}
