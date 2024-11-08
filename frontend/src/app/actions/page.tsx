'use client'

import { useRouter } from 'next/navigation'

import { FC, useEffect } from 'react'

const PageActionsIndex: FC = () => {
  const router = useRouter()

  useEffect(() => {
    router.push('/actions/swap')
  })

  return null
}

export default PageActionsIndex
