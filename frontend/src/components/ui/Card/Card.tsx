import { HTMLAttributes } from 'react'

import clsx from 'clsx'

import type { DarkColor } from '@/components/ui'

import styles from './Card.module.scss'

type CardProps = {
  background?: DarkColor
} & HTMLAttributes<HTMLDivElement>

export function Card({ background = 'dark-60', className, children, ...props }: CardProps) {
  const cardClassName = clsx(
    styles.container,
    {
      [styles[background.split('-').join('--')]]: background,
    },
    className
  )
  return (
    <div className={cardClassName} {...props}>
      {children}
    </div>
  )
}
