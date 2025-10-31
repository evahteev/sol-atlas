'use client'

import { FC, HTMLAttributes } from 'react'

import clsx from 'clsx'

import styles from './Loader.module.scss'

export const Loader: FC<HTMLAttributes<HTMLDivElement> & { isActive?: boolean }> = ({
  isActive = true,
  ...props
}) => {
  return (
    <div
      {...props}
      className={clsx(styles.container, props.className, {
        [styles.active]: isActive,
        [styles.pending]: !isActive,
      })}>
      <div className={styles.indicator}>
        <i className={clsx(styles.segment, styles.first)} />
        <i className={clsx(styles.segment, styles.last)} />
      </div>

      {!!props.children && <div className={styles.message}>{props.children}</div>}
    </div>
  )
}
