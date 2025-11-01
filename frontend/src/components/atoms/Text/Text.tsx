import { DetailedHTMLProps, FC, HTMLAttributes } from 'react'

import clsx from 'clsx'

import styles from './Text.module.scss'

export const Text: FC<DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement>> = ({
  className,
  children,
  ...props
}) => {
  return (
    <div className={clsx(styles.container, className)} {...props}>
      {children}
    </div>
  )
}
