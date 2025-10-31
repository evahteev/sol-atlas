import { FC, HTMLAttributes, ReactNode } from 'react'

import clsx from 'clsx'

import Show from '@/components/ui/Show'

import styles from './Display.module.scss'

type DisplayProps = HTMLAttributes<HTMLDivElement> & {
  caption?: ReactNode
  header?: ReactNode
  footer?: ReactNode
}

export const Display: FC<DisplayProps> = ({ className, caption, header, footer, children }) => {
  return (
    <div className={clsx(styles.container, className)}>
      <Show if={caption || header}>
        <div className={styles.header}>
          <Show if={caption}>
            <strong className={styles.caption}>{caption}</strong>
          </Show>
          <Show if={header}>
            <div className={styles.tools}>{header}</div>
          </Show>
        </div>
      </Show>
      <div className={styles.body}>{children}</div>
      <Show if={footer}>
        <div className={styles.footer}>{footer}</div>
      </Show>
    </div>
  )
}
