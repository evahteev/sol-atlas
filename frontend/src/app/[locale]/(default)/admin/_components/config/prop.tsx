'use client'

import { FC, ReactNode, createElement } from 'react'

import clsx from 'clsx'

import Copy from '@/components/ui/Copy'

import styles from './prop.module.scss'

export type PageCommunityConfigPropProps = {
  icon?: ReactNode
  caption: ReactNode
  value?: string
  className?: string
  type: 'url' | 'text' | 'number'
}

export const PageCommunityConfigProp: FC<PageCommunityConfigPropProps> = ({
  className,
  icon,
  caption,
  value,
  type,
}) => {
  const content = createElement(
    type === 'url' ? 'a' : 'span',
    {
      className: clsx(styles.value, styles[type]),
      ...(type === 'url' ? { href: value, target: '_blank' } : {}),
    },
    value
  )

  return (
    <div className={clsx(styles.container, className)}>
      <span className={styles.icon}>{icon}</span> <span className={styles.caption}>{caption}</span>{' '}
      <span className={styles.content}>
        {content} <Copy size="md" text={value || ''} className={styles.copy} />
      </span>
    </div>
  )
}
