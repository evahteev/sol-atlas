import { FC } from 'react'

import clsx from 'clsx'
import DOMPurify from 'isomorphic-dompurify'
import { marked } from 'marked'

import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'
import Show from '@/components/ui/Show'
import IconDone from '@/images/icons/success.svg'

import styles from './QuestTask.module.scss'

type QuestHistoryTask = {
  title: string
  description?: string | null
  className?: string
}

export const QuestHistoryTask: FC<QuestHistoryTask> = ({ title, description, className }) => {
  const parsedMarkup = DOMPurify.sanitize(
    marked.parse(description ?? '', {
      async: false,
    }) as string
  )

  return (
    <>
      <Card className={clsx(styles.container, styles.completed, className)} tabIndex={0}>
        <div className={styles.body}>
          <Caption variant="body" size="sm" strong className={styles.title}>
            {title}
          </Caption>
          <Show if={description}>
            <Caption
              size="xs"
              className={styles.subtitle}
              dangerouslySetInnerHTML={{ __html: parsedMarkup }}
            />
          </Show>
        </div>
        <div className={styles.footer}>
          <IconDone className={styles.icon} />
        </div>
      </Card>
    </>
  )
}
