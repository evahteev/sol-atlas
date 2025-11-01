'use client'

import Image from 'next/image'
import Link from 'next/link'

import clsx from 'clsx'
import { env } from 'next-runtime-env'
import { erc20Abi, formatEther } from 'viem'
import { base } from 'viem/chains'
import { useReadContract } from 'wagmi'

import Value from '@/components/atoms/Value'
import Banner from '@/components/composed/Banner'
import { BannerProps } from '@/components/composed/Banner/Banner'
import { GURU_BASE_ADDRESS, GURU_CHEST_ADDRESS } from '@/components/ui/SwapFrame/settings'
import { formatNumber } from '@/utils/numbers'

import imageChest from './assets/chest.file.svg'

import styles from './chest.module.scss'

if (!env('NEXT_PUBLIC_GURU_CHEST_ADDRESS')) {
  // throw new Error('NEXT_PUBLIC_GURU_CHEST_ADDRESS is required')
}

export const TasksChest = ({ className, children, ...props }: BannerProps) => {
  const { data: guruChestBalance } = useReadContract({
    abi: erc20Abi,
    address: GURU_BASE_ADDRESS,
    chainId: base.id,
    functionName: 'balanceOf',
    args: [GURU_CHEST_ADDRESS],
  })

  return (
    <Banner
      {...props}
      image={<Image src={imageChest} className={styles.icon} alt="" />}
      className={clsx(styles.container, className)}>
      <div>{children}</div>

      <Link
        href={`https://base.dex.guru/address/${GURU_CHEST_ADDRESS.toLowerCase()}`}
        rel="noreferrer noopener"
        target="_blank">
        <Value
          size="md"
          value={guruChestBalance ? `+${formatNumber(formatEther(guruChestBalance))}` : '–'}
          suffix={<>&nbsp;$GURU (BASE)</>}
          className={styles.value}
        />
      </Link>
    </Banner>
  )
}
