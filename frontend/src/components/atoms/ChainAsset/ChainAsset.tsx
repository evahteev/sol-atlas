'use client'

import { createElement } from 'react'

import clsx from 'clsx'

import ImageFallback from '@/components/atoms/ImageFallback'
import Show from '@/components/ui/Show'
import IconUnknown from '@/images/emoji/hmm.svg'
import { removeUnprintable } from '@/utils'

import styles from './ChainAsset.module.scss'

type ChainAssetProps = {
  className?: string
  name: string | null
  logo?: string | null
  description: string
  size?: 'md' | 'lg' | 'sm'
  color?: string
  href?: string
  onlyAvatar?: boolean
}

export function ChainAsset({
  className,
  name,
  logo,
  href,
  color,
  onlyAvatar,
  description,
  size = 'lg',
}: ChainAssetProps) {
  const content = (
    <>
      <span className={styles.avatar}>
        <Show if={!logo}>
          <span className={styles.icon}>
            <IconUnknown className={styles.image} />
          </span>
        </Show>

        {!!logo && (
          <span className={styles.icon}>
            <ImageFallback
              className={styles.image}
              src={logo}
              alt={removeUnprintable(name ?? '')}
              width={32}
              height={32}
              fallback={<IconUnknown className={styles.image} />}
            />
          </span>
        )}
      </span>

      <Show if={!onlyAvatar}>
        <span className={styles.body}>
          <span className={styles.caption}>{description}</span>
        </span>
      </Show>
    </>
  )

  return createElement(
    href ? 'a' : 'span',
    {
      className: clsx(styles.container, styles[size], className),
      href,
      style: { '--network-color': color },
    },
    content
  )
}
