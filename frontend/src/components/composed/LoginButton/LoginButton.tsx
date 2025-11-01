'use client'

import { FC } from 'react'

import clsx from 'clsx'
import { useTranslations } from 'next-intl'
import { base } from 'thirdweb/chains'
import { ConnectButton, ConnectButtonProps, useActiveWalletChain } from 'thirdweb/react'
import { Wallet } from 'thirdweb/wallets'

import { ButtonSize, ButtonVariant } from '@/components/ui/Button'
import { thirdwebConnectBaseConfig } from '@/config/thirdweb'
import { useConnectHandler } from '@/hooks/useConnectHandler'

import styles from './LoginButton.module.scss'

export type LoginButtonProps = {
  className?: string
  isOutline?: boolean
  isActive?: boolean
  isDisabled?: boolean
  isPending?: boolean
  variant?: ButtonVariant
  size?: ButtonSize
  isBlock?: boolean
  connectButtonOptions?: ConnectButtonProps['connectButton']
  detailsButtonOptions?: ConnectButtonProps['detailsButton']
  connectModalOptions?: ConnectButtonProps['connectModal']
  onConnectOverride?: (wallet: Wallet) => void | Promise<void>
} & Partial<Omit<ConnectButtonProps, 'client' | 'wallets' | 'accountAbstraction' | 'onConnect'>>

export const LoginButton: FC<LoginButtonProps> = ({
  className,
  isActive,
  isPending,
  isDisabled,
  variant = 'default',
  size = 'sm',
  isBlock,
  isOutline,
  connectButtonOptions,
  detailsButtonOptions,
  connectModalOptions,
  ...rest
}) => {
  const t = useTranslations('Auth')
  const { onConnectHandler } = useConnectHandler()
  const chain = useActiveWalletChain()
  const buttonClassName = clsx(
    styles.button,
    styles[variant],
    styles[size],
    {
      [styles.block]: isBlock,
      [styles.outline]: isOutline,
      [styles.active]: isActive,
      [styles.pending]: isPending,
      [styles.disabled]: isDisabled,
    },
    className
  )

  return (
    <ConnectButton
      connectButton={{
        label: t('signIn'),
        className: clsx(styles.button, buttonClassName),
        style: { borderRadius: '10px', minHeight: '10px' },
        ...connectButtonOptions,
      }}
      detailsButton={{ ...detailsButtonOptions, className: className }}
      connectModal={connectModalOptions}
      {...thirdwebConnectBaseConfig}
      onConnect={onConnectHandler}
      accountAbstraction={{
        chain: base,
        sponsorGas: chain?.id === base.id,
      }}
      {...rest}
    />
  )
}
