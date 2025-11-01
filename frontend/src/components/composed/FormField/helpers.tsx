import { ReactNode, createElement } from 'react'

import clsx from 'clsx'

import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
import TooltipAnchor from '@/components/ui/TooltipAnchor'

import styles from './FormField.module.scss'

export const getFieldInputableWrapper = (
  element: 'div' | 'label' | string = 'div',
  {
    caption,
    className,
    tooltip,
    type,
    field,
    children,
  }: {
    caption: ReactNode
    className?: string
    tooltip?: string
    type?: string
    field: ReactNode
    children?: ReactNode
  }
): ReactNode => {
  return createElement(
    element,
    { className: clsx(styles.container, styles.inputable, styles[type ?? ''], className) },
    <>
      {!!caption && (
        <span className={styles.header}>
          <Caption size="sm" className={styles.caption}>
            {caption}
          </Caption>{' '}
          <Show if={tooltip}>
            <TooltipAnchor text={tooltip} />
          </Show>
        </span>
      )}
      <span className={styles.body}>{field}</span>

      {children}
    </>
  )
}
