import Image from 'next/image'
import Link from 'next/link'

import { FC } from 'react'

import clsx from 'clsx'

import Value from '@/components/atoms/Value'
import Show from '@/components/ui/Show'
import { ChainModel } from '@/models/chain'
import { NFTCollectionBalance } from '@/models/nft'
import { buildOpenSeaUrlFromCAIP } from '@/utils/chains'

import styles from './NFTCollection.module.scss'

type NFTCollectionProps = {
  className?: string
  collection: NFTCollectionBalance
  chains: ChainModel[]
}

export const NFTCollection: FC<NFTCollectionProps> = ({ className, collection, chains }) => {
  const { collectionName, caipAddress, nftBalance, chainId } = collection

  const network = chains.find((chain) => chain.id === chainId)
  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.header}>
        <strong className={styles.title}>{collectionName}</strong>{' '}
        <span className={styles.network}>
          <Show if={network?.logo_uri}>
            <Image
              src={network?.logo_uri || ''}
              className={styles.networkImage}
              alt={network?.name || ''}
              width={20}
              height={20}
            />
          </Show>
          {network?.description}
        </span>{' '}
        <Value className={styles.count} value={nftBalance.length} suffix={<>&nbsp;NFT</>} />
      </div>
      <div className={styles.body}>
        <ul className={styles.list}>
          {nftBalance.map((nft) => {
            const openSeaLink = buildOpenSeaUrlFromCAIP(`${caipAddress}/${nft.tokenId}`)
            return (
              <li key={nft.tokenId} className={styles.item}>
                <Link href={openSeaLink} target="_blank" rel="noopener noreferrer">
                  <Image
                    src={nft.metadata.image}
                    alt={nft.metadata.description}
                    className={styles.image}
                    width={120}
                    height={120}
                  />
                </Link>
              </li>
            )
          })}
        </ul>
      </div>
    </div>
  )
}
