import { HTMLAttributes, ReactNode } from 'react'

import clsx from 'clsx'

import Button, { ButtonProps } from '@/components/ui/Button'
import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'

import styles from './Banner.module.scss'

export type BannerProps = HTMLAttributes<HTMLDivElement> & {
  caption?: ReactNode
  actions?: ButtonProps[]
  image: ReactNode
  prefix?: ReactNode
  suffix?: ReactNode
}

export const Banner = ({
  caption,
  actions,
  className,
  children,
  image,
  prefix,
  suffix,
  ...props
}: BannerProps) => {
  return (
    <div className={clsx(styles.container, className)} {...props}>
      {prefix}
      <div className={styles.illustration}>{image}</div>
      <div className={styles.header}>
        <Caption variant="body" size="md" className={styles.title}>
          {caption}
        </Caption>
      </div>
      <div className={styles.body}>
        {children}

        <Show if={actions?.length}>
          <div className={styles.actions}>
            {actions?.map((action, idx) => (
              <Button
                key={idx}
                size="sm"
                variant="primary"
                isOutline
                className={clsx(styles.action, action?.className)}
                {...action}>
                {action?.children}
              </Button>
            ))}
          </div>
        </Show>
      </div>
      {suffix}
    </div>
  )
}
