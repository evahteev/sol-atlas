'use client'

import Link from 'next/link'

import { DetailedHTMLProps, HTMLAttributes } from 'react'

import clsx from 'clsx'

import ImageFallback from '@/components/atoms/ImageFallback'
import Table from '@/components/ui/Table'
import { useQueryResponse } from '@/hooks/warehouse/useQueryResponse'
import { TWarehouseQueryResponse } from '@/services/warehouse-redash/types'
import { formatNumber } from '@/utils/numbers'

import styles from './table.module.scss'

export const PageLauncherDashboardTable = ({
  className,
  initialData,
}: DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement> & {
  initialData?: TWarehouseQueryResponse
}) => {
  const { result, isLoading } = useQueryResponse({
    queryId: 'live_apps_leaderboard',
    maxAge: 0,
    refetchInterval: 5 * 60 * 1000,
    initialData,
  })

  const data = result?.data?.rows
  const isLoadingAndEmpty = isLoading && !data?.length

  return (
    <Table
      className={clsx(styles.container, className)}
      classNameBody={styles.body}
      isLoading={isLoadingAndEmpty}
      data={data || Array(3).fill({})}
      classNameTCell={styles.cell}
      rowProps={{
        className: styles.row,
      }}
      columns={[
        {
          title: 'Rank',
          render: ({ data }) => (
            <span className={styles.rank} data-rank={formatNumber(data.rank || 0)}>
              {data.rank || 0}
            </span>
          ),
        },
        {
          title: 'Community',
          render: ({ data }) => (
            <div className={styles.community}>
              <Link href={`${data.url || ''}`} className={styles.link}>
                <ImageFallback
                  className={styles.image}
                  src={`${data.image_url || ''}`}
                  fallback={<span className={styles.image} />}
                />
                <strong className={styles.caption}>{data.community || '?'}</strong>
              </Link>{' '}
              <span className={styles.description}>{data.description || ''}</span>
            </div>
          ),
        },
        {
          title: 'Members',
          type: 'number',
          render: ({ data }) => (
            <span className={styles.value}>{formatNumber(data.members || 0)}</span>
          ),
        },
        {
          title: 'CAPs, 24h',
          type: 'number',
          tooltip: 'Community Action Points earned in the last 24 hours',
          render: ({ data }) => (
            <span className={styles.value}>{formatNumber(data.caps_24h || 0)}</span>
          ),
        },
        {
          title: 'Actions, 24h',
          type: 'number',
          render: ({ data }) => (
            <span className={styles.value}>{formatNumber(data.actions_24h || 0)}</span>
          ),
        },
        {
          title: 'AIGURU',
          type: 'number',
          render: ({ data }) => (
            <span className={styles.value}>{formatNumber(data.aiguru || 0)}</span>
          ),
        },
      ]}
    />
  )
}
