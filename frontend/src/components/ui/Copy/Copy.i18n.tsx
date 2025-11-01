'use client'

import { FC, MouseEventHandler } from 'react'

import clsx from 'clsx'
import { useTranslations } from 'next-intl'
import { toast } from 'react-toastify'

import IconCopy from '@/images/icons/copy.svg'

import Button, { ButtonProps } from '../Button'

import styles from './Copy.module.scss'

type CopyProps = ButtonProps & {
  href?: never
  text: string
}

export const CopyI18n: FC<CopyProps> = ({
  className,
  text,
  variant = 'clear',
  size = 'xxs',
  isOutline = true,
  ...props
}) => {
  const t = useTranslations('UI')

  const handleClick: MouseEventHandler<HTMLButtonElement> = (e): void => {
    navigator.clipboard
      .writeText(text)
      .then(() => {
        toast.success(t('copiedToClipboard'), {
          toastId: 'clipboard-toast',
          icon: <IconCopy className={styles.success} />,
        })
      })
      .catch(() => {
        toast.error(t('copyFailed'), {
          toastId: 'clipboard-toast',
        })
      })
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
