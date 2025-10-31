'use client'

import { FC, MouseEventHandler } from 'react'

import clsx from 'clsx'

import IconCopy from '@/images/icons/copy.svg'

import Button, { ButtonProps } from '../Button'
import { doCopyToClipboard } from './utils'

import styles from './Copy.module.scss'

type CopyProps = ButtonProps & {
  href?: never
  text: string
}

export const Copy: FC<CopyProps> = ({
  className,
  text,
  variant = 'clear',
  size = 'xxs',
  isOutline = true,
  ...props
}) => {
  const handleClick: MouseEventHandler<HTMLButtonElement> = (e): void => {
    doCopyToClipboard(text)
    props.onClick?.(e)
  }

  return (
    <Button
      {...props}
      variant={variant}
      size={size}
      isOutline={isOutline}
      icon={<IconCopy className={styles.icon} />}
      className={clsx(styles.button, className)}
      onClick={handleClick}
    />
  )
}
