import clsx from 'clsx'

import { Caption, CaptionProps, Show } from '..'

import styles from './Burns.module.scss'

export function Burns({ children, size, strong, variant, className }: CaptionProps) {
  const unit = process.env.NEXT_PUBLIC_APP_CURRENCY

  return (
    <div className={clsx(styles.container, className)}>
      <Caption size={size} strong={strong} variant={variant} className={styles.value}>
        {children}
      </Caption>
      <Show if={unit}>
        <>
          {' '}
          <Caption size={size} strong={strong} variant={variant} className={styles.unit}>
            {unit}
          </Caption>
        </>
      </Show>
    </div>
  )
}
