import { FC } from 'react'

import clsx from 'clsx'

import Message from '@/components/ui/Message'
import Show from '@/components/ui/Show'
import { ChainModel } from '@/models/chain'
import { NFTCollectionBalance } from '@/models/nft'

import NFTCollection from '../NFTCollection'

import styles from './NFTsList.module.scss'

type NFTsListProps = {
  className?: string
  chains: ChainModel[]
  data?: NFTCollectionBalance[]
}

export const NFTsList: FC<NFTsListProps> = ({ className, chains, data }) => {
  const count =
    data?.reduce((acc, collection) => acc + (collection?.nftBalance?.length || 0), 0) ?? 0

  if (!count) {
    return null
  }

  return (
    <div className={clsx(styles.container, className)}>
      <Show if={!count}>
        <Message type="info">This account currently has no any NFT</Message>
      </Show>

      <ul className={styles.list}>
        {data?.map((nft) => {
          if (!nft?.nftBalance.length) {
            return null
          }

          return (
            <li key={nft?.caipAddress} className={styles.item}>
              <NFTCollection className={styles.collection} collection={nft} chains={chains} />
            </li>
          )
        })}
      </ul>
    </div>
  )
}
