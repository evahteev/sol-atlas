'use client'

import { FC, useEffect } from 'react'

import { backButton } from '@telegram-apps/sdk'

export const TelegramBackButton: FC<{ onClick: () => void; isShow?: boolean }> = ({
  onClick,
  isShow = true,
}) => {
  useEffect(() => {
    if (!backButton.isMounted()) {
      backButton.mount()
    }
    backButton.onClick(onClick)

    return () => {
      if (backButton.isMounted()) {
        backButton.hide()
        backButton.unmount()
      }
      backButton.offClick(onClick)
    }
  }, [onClick])

  useEffect(() => {
    backButton[isShow ? 'show' : 'hide']()
  }, [isShow])

  return null
}
