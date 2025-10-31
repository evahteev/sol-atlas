import { DetailedHTMLProps, HTMLAttributes } from 'react'

import clsx from 'clsx'

import styles from './Card.module.scss'

export function Card({
  className,
  children,
  ...props
}: DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement>) {
  const cardClassName = clsx(styles.container, className)
  return (
    <div className={cardClassName} {...props}>
      {children}
    </div>
  )
}
