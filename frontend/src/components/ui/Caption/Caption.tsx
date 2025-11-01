import { HTMLAttributes } from 'react'

import clsx from 'clsx'

import { Size } from '../types'

import styles from './Caption.module.scss'

type Variant = 'header' | 'body' | 'numbers'

export type CaptionProps = {
  size?: Size
  variant?: Variant
  strong?: boolean
  decorated?: 'fire'
} & HTMLAttributes<HTMLDivElement>

export function Caption({
  children,
  size = 'md',
  variant = 'body',
  strong,
  className,
  decorated,
}: CaptionProps) {
  const captionClassName = clsx(
    styles.container,
    styles[variant],
    styles[size],
    {
      [styles[decorated as string]]: decorated,
      [styles.strong]: strong,
    },
    className
  )
  return <span className={captionClassName}>{children}</span>
}
