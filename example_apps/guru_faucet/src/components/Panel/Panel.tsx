import { FC, HTMLAttributes, PropsWithChildren, PropsWithRef, ReactNode } from 'react'

import clsx from 'clsx'

import styles from './Panel.module.scss'

export type PanelProps = PropsWithRef<
  PropsWithChildren<
    HTMLAttributes<HTMLDivElement> & {
      caption?: ReactNode
      subtitle?: ReactNode
      footer?: ReactNode | ReactNode[]
      bodyClassName?: string
      icon?: ReactNode
    }
  >
>

export const Panel: FC<PanelProps> = ({
  children,
  caption,
  icon,
  subtitle,
  className,
  footer,
  bodyClassName,
  ...props
}) => {
  return (
    <div {...props} className={clsx(styles.container, className)}>
      {(!!caption || !!subtitle) && (
        <div className={styles.header}>
          {!!icon && <span className={styles.icon}>{icon}</span>}
          {!!caption && <h2 className={styles.title}>{caption}</h2>}
          {!!subtitle && <span className={styles.subtitle}>{subtitle}</span>}
        </div>
      )}

      <div className={clsx(styles.body, bodyClassName)}>{children}</div>
      {!!footer && <div className={styles.footer}>{footer}</div>}
    </div>
  )
}
