import { FC, Suspense } from 'react'

import clsx from 'clsx'
import { sanitize } from 'isomorphic-dompurify'
import { marked } from 'marked'

import { TWarehouseQueryParam, TWarehouseWidget } from '@/actions/warehouse/types'
import Loader from '@/components/atoms/Loader'
import { Caption } from '@/components/ui'

import { WarehouseDashboardWidgetVisualization } from './WarehouseDashboardWidgetVisualization'

import styles from './WarehouseDashboardWidget.module.scss'

export type WarehouseDashboardWidgetProps = {
  className?: string
  widget: TWarehouseWidget
  params?: Record<string, TWarehouseQueryParam>
}

export const WarehouseDashboardWidget: FC<WarehouseDashboardWidgetProps> = ({
  widget: { options, visualization, text },
  className,
  params,
}) => {
  const title = visualization
    ? visualization?.type?.toLowerCase() !== visualization?.name?.toLowerCase()
      ? visualization?.name
      : visualization.query.name
    : undefined

  const parsedMarkup = marked.parse(text, { async: false }) as string

  return (
    <div
      className={clsx(styles.container, className)}
      style={{
        gridColumn: `${options?.position.col + 1} / span ${options?.position.sizeX}`,
        gridRow: `${options?.position.row + 1} / span ${options?.position.sizeY}`,
      }}>
      <div className={styles.header}>
        <Caption variant="header" size="lg" className={styles.title}>
          {title}
        </Caption>
        <Caption variant="body" size="sm" className={styles.description}>
          {visualization?.query?.description}
        </Caption>
      </div>
      {!!text && (
        <div
          className={clsx(styles.text, 'text')}
          dangerouslySetInnerHTML={{
            __html: sanitize(parsedMarkup),
          }}
        />
      )}
      <Suspense
        fallback={
          <div className={styles.empty}>
            <Loader className={styles.suspense} />
          </div>
        }>
        <WarehouseDashboardWidgetVisualization
          visualization={visualization}
          params={params}
          mapping={options.parameterMappings ?? {}}
        />
      </Suspense>
    </div>
  )
}
