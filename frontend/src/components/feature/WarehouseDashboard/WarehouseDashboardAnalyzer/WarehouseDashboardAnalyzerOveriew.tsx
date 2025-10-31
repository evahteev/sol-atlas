'use client'

import { FC, useContext, useEffect, useState } from 'react'

import clsx from 'clsx'
import DOMPurify from 'isomorphic-dompurify'

import Button from '@/components/ui/Button'
import Show from '@/components/ui/Show'
import { useTypewriter } from '@/hooks/useTypewriter'
import IconToggle from '@/images/icons/chevron-down.svg'

import { WarehouseDashboardAnalyzerHistory } from './WarehouseDashboardAnalyzerHistoryProvider'
import { WarehouseDashboardAnalyzerVariants } from './WarehouseDashboardAnalyzerVariants'
import { useDashboardAnalyze } from './hooks'

import styles from './WarehouseDashboardAnalyzerOverview.module.scss'

export const WarehouseDashboardAnalyzerOverview: FC<{
  className?: string
  slug: string
  params?: Record<string, unknown>
}> = ({ className, slug, params }) => {
  const { updateHistory } = useContext(WarehouseDashboardAnalyzerHistory)

  const [currentPrompt, setCurrentPrompt] = useState<string | null>(null)
  const [isShow, setIsShow] = useState(true)

  const { data, isFetching, refetch } = useDashboardAnalyze({
    slug,
    params,
    prompt: currentPrompt,
  })

  useEffect(() => {
    if (data && currentPrompt) {
      updateHistory({ prompt_submitted: currentPrompt, summary: data })
    }
  }, [currentPrompt, data, updateHistory])

  const response = data
    ? DOMPurify.sanitize(data.trim())
    : isFetching
      ? 'Hmmm... Let me think...'
      : data === null
        ? 'Ooops! Sorry, I got my circuits shorted...'
        : 'What do you want to know today?'

  const [printed, notPrinted] = useTypewriter(
    response.replace(' - ', ' – ').replace(' "', ' “').replace('"', '”')
  )

  const handleToggle = () => {
    setIsShow(!isShow)
  }

  return (
    <div className={clsx(styles.container, { [styles.toggled]: !isShow }, className)}>
      <div className={styles.body}>
        <Button
          icon={<IconToggle className={clsx(styles.toggleIcon, { [styles.toggled]: !isShow })} />}
          variant="clear"
          size="sm"
          className={clsx(styles.toggle, { [styles.toggled]: !isShow })}
          onClick={handleToggle}
        />
        <Show if={!isShow}>
          <div className={styles.response}>
            <div className={styles.responseText}>
              Let&apos;s talk! I have many thoughts on this data.
            </div>
          </div>
        </Show>

        <Show if={isShow}>
          <div className={styles.response}>
            <Show if={currentPrompt}>
              <div className={styles.responseSubject}>{currentPrompt}</div>
            </Show>

            <div className={styles.responseText}>
              <Show if={printed}>
                <span className={styles.printed}>{printed}</span>
                <span className={styles.notPrinted}>{notPrinted}</span>
              </Show>

              <Show if={!isFetching && data === null}>
                <Button
                  caption="Retry?"
                  size="sm"
                  className={styles.retru}
                  onClick={() => {
                    refetch()
                  }}
                />
              </Show>
            </div>

            {isFetching && (
              <div className={styles.processing}>
                <span />
                <span />
              </div>
            )}
          </div>

          <WarehouseDashboardAnalyzerVariants
            slug={slug}
            params={params}
            onSubmit={(value: string) => {
              setCurrentPrompt(value)
            }}
          />
        </Show>
      </div>
    </div>
  )
}
