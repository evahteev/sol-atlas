'use client'

import { FC, HTMLAttributes } from 'react'

import clsx from 'clsx'

import styles from './Loader.module.scss'

export const Loader: FC<HTMLAttributes<HTMLDivElement>> = (props) => {
  return (
    <div {...props} className={clsx(styles.container, props.className)}>
      <i className={styles.segment} />
      <i className={styles.segment} />
    </div>
  )
}
