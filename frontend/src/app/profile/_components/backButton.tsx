'use client'

import { useRouter } from 'next/navigation'

import { FC, useState } from 'react'

import TelegramBackButton from '@/components/feature/telegram/BackButton'

export const ProfileBackButton: FC = () => {
  const [isClicked, setIsClicked] = useState(false)

  const router = useRouter()
  const handleClick = () => {
    if (!isClicked) {
      router.back()
      setIsClicked(true)
    }
  }

  return <TelegramBackButton onClick={handleClick} />
}
