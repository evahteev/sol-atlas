'use client'

import Image from 'next/image'

import { FC, useState } from 'react'

import IconUnknown from '@/images/emoji/hmm.svg'
import { TokenTagModel } from '@/models/token'

export const TokensTagsCloudTagIcon: FC<{ tag: TokenTagModel; className?: string }> = ({
  tag,
  className,
}) => {
  const [isError, setIsError] = useState(false)

  if (!tag.logo_uri) {
    return null
  }

  if (isError) {
    return <IconUnknown className={className} />
  }

  return (
    <Image
      className={className}
      src={tag.logo_uri}
      alt={tag.short_name}
      width={32}
      height={32}
      onError={() => setIsError(true)}
    />
  )
}
