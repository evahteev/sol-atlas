'use client'

import { FC, useState } from 'react'

import clsx from 'clsx'

import Button, { ButtonProps } from '@/components/ui/Button'
import Dialog from '@/components/ui/Dialog'
import IconSwap from '@/images/icons/swap.svg'

import { TokenOverviewTokenSwapContent, TokenOverviewTokenSwapContentProps } from './content'

import styles from './swap.module.scss'

type TokenOverviewTokenSwapProps = ButtonProps & TokenOverviewTokenSwapContentProps

export const TokenOverviewTokenSwap: FC<TokenOverviewTokenSwapProps> = ({
  variant,
  size,
  token,
  className,
  ...props
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const handleOpen = () => {
    setIsOpen(true)
  }

  const handleClose = () => {
    setIsOpen(false)
  }

  return (
    <>
      <Button
        {...props}
        variant={variant ?? 'primary'}
        size={size ?? 'sm'}
        className={clsx(styles.action, className)}
        icon={<IconSwap className={clsx(styles.icon, styles.swap)} />}
        onClick={handleOpen}
      />

      <Dialog isOpen={isOpen} onClose={handleClose} isMaximized className={styles.dialog}>
        <TokenOverviewTokenSwapContent className={styles.body} token={token} />
      </Dialog>
    </>
  )
}
