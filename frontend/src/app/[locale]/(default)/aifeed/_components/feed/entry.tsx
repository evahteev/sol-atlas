'use client'

import { DetailedHTMLProps, FC, HTMLAttributes } from 'react'

import clsx from 'clsx'

import { WarehouseDashboardBySlugClient } from '@/components/feature/WarehouseDashboard'
import Card from '@/components/ui/Card'
import TimerCountdown from '@/components/ui/TimerCountdown'
import IconAI from '@/images/icons/aichat.svg'

import styles from './entry.module.scss'

type FeedTranslations = {
  aiAgent: string
  timeAgo: string
}

export const PageMainFeedEntry: FC<
  DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement> & {
    slug: string
    date: string
    translations: FeedTranslations
  }
> = ({ className, slug, date, translations, ...props }) => {
  const t = (key: keyof FeedTranslations) => translations[key]
  const dateTime = new Date(date ?? undefined)

  return (
    <Card {...props} className={clsx(styles.entry, className)}>
      <div className={styles.header}>
        <div className={styles.author}>
          <span className={styles.avatar}>
            <IconAI className={styles.icon} />
          </span>

          <span className={styles.caption}>{t('aiAgent')}</span>
        </div>

        <span className={styles.date}>
          <TimerCountdown
            className={styles.timer}
            timestamp={dateTime.getTime()}
            isCompact
            suffix={t('timeAgo')}
          />
        </span>
      </div>
      <div className={styles.body}>
        <WarehouseDashboardBySlugClient slug={slug} />
      </div>
    </Card>
  )
}
