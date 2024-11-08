'use client'

import { FC, MouseEventHandler, useContext, useEffect } from 'react'

import clsx from 'clsx'

import { Button, Show } from '@/components/ui'

import { WarehouseDashboardAnalyzerHistoryEntryProps } from './WarehouseDashboardAnalyzer'
import { WarehouseDashboardAnalyzerHistory } from './WarehouseDashboardAnalyzerHistoryProvider'
import { useDashboardPrompts } from './hooks'

import styles from './WarehouseDashboardAnalyzerVariants.module.scss'

export const WarehouseDashboardAnalyzerVariants: FC<{
  slug: string
  params?: Record<string, unknown>
  onSubmit: (value: string) => void
  history?: WarehouseDashboardAnalyzerHistoryEntryProps[]
  className?: string
  isDisabled?: boolean
}> = ({ slug, params, onSubmit, history, isDisabled, className }) => {
  const { prompts, updatePrompts } = useContext(WarehouseDashboardAnalyzerHistory)
  const { data, isFetching, refetch } = useDashboardPrompts(slug, params, history, prompts)

  useEffect(() => {
    if (!data?.length) {
      return
    }

    updatePrompts(data)
  }, [data])

  return (
    <div className={clsx(styles.container, { [styles.pending]: isFetching }, className)}>
      <Show if={prompts?.length}>
        <div className={styles.prompts}>
          {data?.map((prompt: string, idx: number) => {
            const handleClick: MouseEventHandler = (e) => {
              onSubmit(prompt)
              const target = e.target as HTMLElement
              if (target) {
                target.scrollIntoView({
                  behavior: 'smooth',
                  inline: 'nearest',
                  block: 'nearest',
                })
              }
            }

            return (
              <Button
                isDisabled={isDisabled}
                size="sm"
                key={idx}
                caption={prompt}
                className={styles.prompt}
                onClick={handleClick}
              />
            )
          })}
        </div>
      </Show>

      <Show if={data === null && !isFetching}>
        <Button
          size="md"
          caption="Failed preparing fresh prompts. Retry?"
          className={styles.prompt}
          onClick={() => {
            refetch()
          }}
        />
      </Show>
    </div>
  )
}
