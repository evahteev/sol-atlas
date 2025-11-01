import { FC, Suspense } from 'react'

import clsx from 'clsx'

import { ChainModel } from '@/models/chain'
import { TokenV3Model } from '@/models/token'

import { TokenOverviewLinksCommunity } from './community'
import { TokenOverviewLinksExplorer } from './explorer'

import styles from './links.module.scss'

export const TokenOverviewLinks: FC<{
  chains: ChainModel[]
  className?: string
  token: TokenV3Model
}> = ({ chains, token, className }) => {
  return (
    <div className={clsx(styles.container, className)}>
      <Suspense>
        <TokenOverviewLinksCommunity token={token} className={styles.community} />
      </Suspense>

      <TokenOverviewLinksExplorer token={token} chains={chains} className={styles.nav} />
    </div>
  )
}
