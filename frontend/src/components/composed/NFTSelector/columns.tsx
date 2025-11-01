import ChainAsset from '@/components/atoms/ChainAsset'
import ImageFallback from '@/components/atoms/ImageFallback'
import { TableColumnProps } from '@/components/ui/Table/types'
import { ChainModel } from '@/models/chain'

import { NFTCollectionItem } from './types'

import styles from './NFTSelector.module.scss'

export const nftColumns = (chains: ChainModel[]): TableColumnProps<NFTCollectionItem>[] => [
  {
    title: 'NFT Collection',
    render: ({ data }) => {
      const chain = chains.find((chain) => chain.id === data.chainId)
      return (
        <div className={styles.nftCollection}>
          <ImageFallback
            fallback={<div className={styles.nftImage}>?</div>}
            src={data.metadata.image ?? ''}
            alt={data.metadata.description ?? ''}
            className={styles.nftImage}
            width={120}
            height={120}
          />{' '}
          {data.collectionName}{' '}
          <ChainAsset
            className={styles.nftChain}
            logo={chain?.logo_uri}
            name={chain?.name || 'UNKNOWN'}
            description={chain?.description || 'UNKNOWN'}
            size="sm"
            color={chain?.color}
            onlyAvatar
          />
        </div>
      )
    },
    className: styles.colName,
  },
  {
    title: 'Token ID',
    render: ({ data }) => data.tokenId,
    className: styles.colId,
    type: 'number',
  },
]
