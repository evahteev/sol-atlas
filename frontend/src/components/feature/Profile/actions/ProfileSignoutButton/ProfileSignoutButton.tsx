'use client'

import { FC, useCallback } from 'react'

import clsx from 'clsx'
import { signOut } from 'next-auth/react'
import { useActiveWallet, useDisconnect } from 'thirdweb/react'

import { logout } from '@/actions/thirdweb'
import Button, { ButtonProps } from '@/components/ui/Button'
import { DEFAULT_REDIRECT_PATH } from '@/config/settings'

import styles from './ProfileSignoutButton.module.scss'

type SignoutButtonProps = ButtonProps & {
  //
}

export const ProfileSignoutButton: FC<SignoutButtonProps> = ({ caption, className, ...props }) => {
  const { disconnect } = useDisconnect()
  const wallet = useActiveWallet()
  const handleSignOut = useCallback(async () => {
    if (wallet) {
      disconnect(wallet)
    }
    await logout()
    signOut({ redirectTo: DEFAULT_REDIRECT_PATH })
  }, [disconnect, wallet])
  return (
    <Button
      {...props}
      caption={caption ?? 'Sign Out'}
      onClick={handleSignOut}
      className={clsx(styles.button, className)}
    />
  )
}
