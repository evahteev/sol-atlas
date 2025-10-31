'use client'

import { FC, useState } from 'react'

import { CaipAddress } from '@reown/appkit'
import clsx from 'clsx'
import { env } from 'next-runtime-env'

import FormField from '@/components/composed/FormField'
import NFTSelector from '@/components/composed/NFTSelector'

import styles from './TaskFormFieldNFT.module.scss'

type TaskFormFieldNFTProps = {
  className?: string
  name: string
  caption?: string | null
  account?: string
  address?: CaipAddress
  collectionList?: CaipAddress[]
}

const contracts: CaipAddress[] = JSON.parse(env('NEXT_PUBLIC_APP_COMMUNITY_NFT_ADDRESSES') || '[]')

export const TaskFormFieldNFT: FC<TaskFormFieldNFTProps> = ({
  className,
  name,
  caption,
  account,
  address,
  collectionList,
}) => {
  const [currentNFT, setCurrentNFT] = useState<CaipAddress | undefined>()

  const onSelectChange = (nft?: CaipAddress) => {
    setCurrentNFT(nft)
  }

  return (
    <>
      <FormField className={clsx(styles.container, className)} type="display" caption={caption}>
        <NFTSelector
          account={account}
          address={address}
          className={styles.selector}
          onNFTChange={onSelectChange}
          collectionList={collectionList ?? contracts}
        />

        <input value={currentNFT ?? ''} name={name} type="hidden" />
      </FormField>
    </>
  )
}
