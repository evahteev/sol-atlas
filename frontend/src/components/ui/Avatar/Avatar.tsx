import Image from 'next/image'

import { HTMLAttributes } from 'react'

import clsx from 'clsx'

import styles from './Avatar.module.scss'

export type AvatarProps = {
  src: string
  alt: string
} & HTMLAttributes<HTMLDivElement>

export function Avatar({ src, alt, className }: AvatarProps) {
  return (
    <div className={clsx(styles.container, className)}>
      <Image className={styles.image} src={src} width={40} height={40} alt={alt} />
    </div>
  )
}
