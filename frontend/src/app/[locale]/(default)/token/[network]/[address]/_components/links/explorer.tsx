'use client'

import Image from 'next/image'

import { FC } from 'react'

import clsx from 'clsx'

import { ButtonProps } from '@/components/ui/Button'
import ButtonGroup from '@/components/ui/ButtonGroup'
import IconNansen from '@/images/apps/nansen.svg'
import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'

import styles from './links.module.scss'

export const TokenOverviewLinksExplorer: FC<{
  chains: ChainModel[]
  token: TokenV3Model
  className?: string
}> = ({ chains, token, className }) => {
  const blockExplorerData = chains?.find((item) => item.name === token.network)?.block_explorer

  if (!blockExplorerData) {
    return null
  }

  const buttons: ButtonProps[] = [
    {
      className: styles.link,
      href: `https://pro.nansen.ai/token-god-mode?token_address=${token.address}`,
      rel: 'noreferrer noopener',
      target: '_blank',
      icon: <IconNansen className={styles.icon} />,
    },
  ]

  if (blockExplorerData) {
    buttons.push({
      className: styles.link,
      href: `${blockExplorerData.url}${blockExplorerData.token_path}/${token.address.toLowerCase()}`,
      rel: 'noreferrer noopener',
      target: '_blank',
      icon: (
        <Image
          src={blockExplorerData.logo_uri}
          alt={blockExplorerData.display_name}
          data-tooltip-content={blockExplorerData.display_name}
          data-tooltip-id="app-tooltip"
          width={16}
          height={16}
          className={styles.icon}
        />
      ),
    })
  }

  return (
    <ButtonGroup
      isOutline
      size="sm"
      buttons={buttons}
      className={clsx(styles.explorers, className)}
    />
  )
}
