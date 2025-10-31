import { FC } from 'react'

import clsx from 'clsx'
import DOMPurify from 'isomorphic-dompurify'
import { marked } from 'marked'

import Text from '@/components/atoms/Text'
import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'
import Show from '@/components/ui/Show'
import { TWarehouseQueryParam, TWarehouseWidget } from '@/services/warehouse-redash/types'

import { WarehouseDashboardWidgetVisualization } from './WarehouseDashboardWidgetVisualization'

import styles from './WarehouseDashboardWidget.module.scss'

export type WarehouseDashboardWidgetProps = {
  className?: string
  widget: TWarehouseWidget
  params?: Record<string, TWarehouseQueryParam>
  allowUpdate?: boolean
}

export const WarehouseDashboardWidget: FC<WarehouseDashboardWidgetProps> = ({
  widget,
  className,
  params,
  allowUpdate,
}) => {
  const { options, visualization, text } = widget
  const nameType = visualization?.name?.toLowerCase().split('_')

  const title =
    visualization?.name && visualization?.type?.toLowerCase() !== nameType[0]
      ? visualization.name
      : visualization?.query?.name

  const parsedMarkup = marked.parse(text, { async: false }) as string

  return (
    <Card
      className={clsx(styles.container, className)}
      style={{
        gridColumn: `${options?.position.col + 1} / span ${options?.position.sizeX}`,
        gridRow: `${options?.position.row + 1} / span ${options?.position.sizeY}`,
      }}>
      <Show if={title || visualization?.query?.description}>
        <div className={styles.header}>
          <Show if={title}>
            <Caption variant="header" size="lg" className={styles.title}>
              {title}
            </Caption>
          </Show>

          <Show if={visualization?.query?.description}>
            <Caption variant="body" size="sm" className={styles.description}>
              {visualization?.query?.description}
            </Caption>
          </Show>
        </div>
      </Show>
      {!!text && (
        <Text
          className={clsx(styles.text, 'text')}
          dangerouslySetInnerHTML={{
            __html: DOMPurify.sanitize(parsedMarkup, {
              ADD_TAGS: ['iframe', 'style', 'svg'],
              ADD_ATTR: ['allow', 'allowfullscreen', 'target'],
            }),
          }}
        />
      )}
      <Show if={visualization?.type}>
        <WarehouseDashboardWidgetVisualization
          visualization={visualization}
          params={params}
          mapping={options.parameterMappings ?? {}}
          allowUpdate={allowUpdate}
        />
      </Show>
    </Card>
  )
}
