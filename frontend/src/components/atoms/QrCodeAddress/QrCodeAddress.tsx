'use client'

import Image from 'next/image'
import Link from 'next/link'

import { FC, ReactNode, useEffect, useState } from 'react'

import clsx from 'clsx'
import QRCode from 'qrcode'

import Text from '@/components/atoms/Text'
import Copy from '@/components/ui/Copy'
import Show from '@/components/ui/Show'
import IconCopy from '@/images/icons/copy.svg'

import styles from './QrCodeAddress.module.scss'

type QrCodeAddressProps = {
  className?: string
  address: string
  caption?: ReactNode
}

export const QrCodeAddress: FC<QrCodeAddressProps> = ({
  className,
  address,
  caption = (
    <>
      Use this address to receive tokens in your operational wallet. Compatible with EVM chains
      including Ethereum, Base, BNB Chain, Optimism, Arbitrum, Polygon, and others. See the{' '}
      <Link href="https://docs.dex.guru/data/supported-chains" target="_blank">
        full list of supported chains
      </Link>
    </>
  ),
}) => {
  const [dataURL, setDataURL] = useState<string | null>(null)

  useEffect(() => {
    QRCode.toDataURL(address ?? '', {
      type: 'image/png',
      margin: 1,
    })
      .then((res: string) => setDataURL(res))
      .catch((e) => {
        console.error(e)
        return null
      })
  }, [address])

  return (
    <div className={clsx(styles.container, className)}>
      <div className={styles.header}></div>
      <Text className={styles.description}>{caption}</Text>
      <Show if={dataURL}>
        <Image
          src={dataURL ?? ''}
          alt="Share Link QR Code"
          className={styles.illustration}
          width={320}
          height={320}
        />
      </Show>

      <Show if={!dataURL}>
        <span className={clsx(styles.illustration, styles.loading)} />
      </Show>

      <Copy
        caption={address}
        text={address}
        icon={<IconCopy />}
        isBlock
        isOutline
        variant="primary"
        size="xl"
        className={styles.copy}
        isDisabled={!address}
      />
    </div>
  )
}
