'use client'

import { FC, useContext, useEffect, useRef, useState } from 'react'

import { CaipAddress } from '@reown/appkit'
import clsx from 'clsx'
import { useCombobox } from 'downshift'
import { env } from 'next-runtime-env'

import ChainAsset from '@/components/atoms/ChainAsset'
import ImageFallback from '@/components/atoms/ImageFallback'
import DropdownContent from '@/components/ui/DropdownContent'
import Message from '@/components/ui/Message'
import Show from '@/components/ui/Show'
import Table from '@/components/ui/Table'
import { TableRowProps } from '@/components/ui/Table/types'
import useNftBalances from '@/hooks/useNftBalances'
import IconDown from '@/images/icons/chevron-down.svg'
import { AppContext } from '@/providers/context'

import { nftColumns } from './columns'
import { NFTCollectionItem } from './types'

import styles from './NFTSelector.module.scss'

type NFTSelectorProps = {
  className?: string
  address?: CaipAddress
  account?: string
  onNFTChange?: (address?: CaipAddress) => void
  placeholder?: string
  size?: 'sm' | 'md' | 'lg'
  collectionList?: CaipAddress[]
}

const contracts: CaipAddress[] = JSON.parse(env('NEXT_PUBLIC_APP_COMMUNITY_NFT_ADDRESSES') || '[]')

export const NFTSelector: FC<NFTSelectorProps> = ({
  className,
  address,
  account,
  placeholder = 'Search NFT by collection name or address',
  onNFTChange,
  size = 'lg',
  collectionList,
}) => {
  const { chains } = useContext(AppContext)

  const [currentNFT, setCurrentNFT] = useState<NFTCollectionItem | undefined>()
  const [currentQuery, setCurrentQuery] = useState('')

  const { data: nftBalances, isFetching: isFetchingNftBalances } = useNftBalances({
    contracts: collectionList ?? contracts,
    address: account,
    refetchInterval: 60 * 1000,
  })

  const searchQuery = currentQuery.toLowerCase()

  const nftList: NFTCollectionItem[] =
    nftBalances
      ?.filter((collection) => !!collection.nftBalance)
      .map((collection) => collection.nftBalance.map((nft) => ({ ...collection, ...nft })))
      .flat()
      .filter(
        (collection) =>
          !currentQuery ||
          (!!currentQuery &&
            (collection.collectionName?.toLowerCase().includes(searchQuery) ||
              collection.caipAddress?.toLowerCase().includes(searchQuery) ||
              `${collection.tokenId}`.includes(searchQuery)))
      ) ?? []

  useEffect(() => {
    if (address === currentNFT?.caipAddress) {
      return
    }

    onNFTChange?.(address)
  }, [address, currentNFT?.caipAddress, onNFTChange])

  const refContainer = useRef<HTMLDivElement>(null)

  const inputRef = useRef<HTMLInputElement>(null)

  const {
    isOpen,
    getToggleButtonProps,
    getMenuProps,
    highlightedIndex,
    getItemProps,
    getInputProps,
  } = useCombobox({
    items: nftList ?? [],
    itemToString: () => '',
    onInputValueChange: ({ inputValue }) => {
      setCurrentQuery(inputValue.trim() || '')
    },
    onSelectedItemChange: ({ selectedItem }) => {
      if (!selectedItem || selectedItem.caipAddress === currentNFT?.caipAddress) {
        return
      }

      setCurrentNFT(selectedItem)
      onNFTChange?.(`${selectedItem?.caipAddress}/${selectedItem?.tokenId}`)
    },
  })

  const getRowProps = (item?: NFTCollectionItem, index?: number): TableRowProps => {
    if (!item) {
      return {}
    }

    return {
      ...getItemProps({ item, index }),
      className: clsx({
        [styles.hilite]: highlightedIndex === index,
      }),
    }
  }

  const nftChain = chains.find((chain) => chain.id === currentNFT?.chainId)

  return (
    <div
      className={clsx(
        styles.container,
        {
          [styles.open]: isOpen,
          [styles.pending]: isFetchingNftBalances,
        },
        styles[size],
        className
      )}
      ref={refContainer}>
      <div className={styles.body} {...getToggleButtonProps()}>
        <input
          type="text"
          placeholder={placeholder}
          className={styles.input}
          {...getInputProps({ ref: inputRef })}
          autoFocus
        />

        <div className={styles.token}>
          {!!currentNFT && (
            <div className={styles.nftCollection}>
              <ImageFallback
                fallback={<div className={styles.nftImage}>?</div>}
                src={currentNFT.metadata.image ?? ''}
                alt={currentNFT.metadata.description ?? ''}
                className={styles.nftImage}
                width={120}
                height={120}
              />{' '}
              {currentNFT.collectionName}{' '}
              <ChainAsset
                className={styles.nftChain}
                logo={nftChain?.logo_uri}
                name={nftChain?.name || 'UNKNOWN'}
                description={nftChain?.description || 'UNKNOWN'}
                size="sm"
                color={nftChain?.color}
                onlyAvatar
              />
            </div>
          )}

          {!currentNFT && <span className={styles.placeholder}>{placeholder}</span>}
        </div>

        <IconDown className={styles.indicator} />
      </div>

      <DropdownContent
        isOpen={isOpen}
        className={clsx(styles.dropdown, {
          [styles.open]: isOpen,
          [styles[size]]: !!styles[size],
        })}
        {...getMenuProps({}, { suppressRefError: true })}
        element={refContainer.current}>
        <Show if={!isFetchingNftBalances && !nftList?.length}>
          <Message type="danger" className={styles.message}>
            No NFTs found
          </Message>
        </Show>

        <Show if={nftList?.length}>
          <Table
            className={styles.table}
            data={nftList}
            classNameTBody={styles.tbody}
            classNameTCell={styles.tcell}
            rowKey={(item) => `${item.caipAddress}-${item.tokenId}`}
            rowProps={getRowProps}
            columns={nftColumns(chains)}
          />
        </Show>
      </DropdownContent>
    </div>
  )
}
