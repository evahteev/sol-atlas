import { DetailedHTMLProps, FC, HTMLAttributes, ReactNode } from 'react'

import clsx from 'clsx'

import Caption from '../Caption'
import Show from '../Show'

import styles from './Section.module.scss'

type SectionProps = DetailedHTMLProps<HTMLAttributes<HTMLElement>, HTMLElement> & {
  caption?: ReactNode

  classNames?: {
    container?: string
    body?: string
    header?: string
    title?: string
  }
}

export const Section: FC<SectionProps> = ({
  caption,
  children,
  className,
  classNames,
  ref,
  ...rest
}) => {
  return (
    <section
      {...rest}
      className={clsx(styles.container, className, classNames?.container)}
      ref={ref}>
      <Show if={caption}>
        <div className={clsx(styles.header, classNames?.header)}>
          <Caption variant="body" size="md" className={styles.title}>
            {caption}
          </Caption>
        </div>
      </Show>

      <div className={clsx(styles.body, classNames?.body)}>{children}</div>
    </section>
  )
}
