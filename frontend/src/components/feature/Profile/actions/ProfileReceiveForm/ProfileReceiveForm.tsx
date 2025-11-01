'use client'

import Image from 'next/image'
import Link from 'next/link'

import { FC, useEffect, useState } from 'react'

import clsx from 'clsx'
import QRCode from 'qrcode'

import Text from '@/components/atoms/Text'
import Button from '@/components/ui/Button'
import Copy from '@/components/ui/Copy'
import Show from '@/components/ui/Show'
import IconCopy from '@/images/icons/copy.svg'

import styles from './ProfileReceiveForm.module.scss'

type ReceiveFormProps = {
  className?: string
  address: string
  onProcessStart: () => void
}

export const ProfileReceiveForm: FC<ReceiveFormProps> = ({
  className,
  address,
  onProcessStart,
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
      <div className={styles.header}>
        <Text className={styles.description}>
          Use this address to receive tokens in your operational wallet. Compatible with EVM chains
          including Ethereum, Base, BNB Chain, Optimism, Arbitrum, Polygon, and others. See the{' '}
          <Link href="https://docs.dex.guru/data/supported-chains" target="_blank">
            full list of supported chains
          </Link>
        </Text>
      </div>

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

      <div className={styles.footer}>
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

        <Button
          href="/topup"
          isBlock
          variant="primary"
          size="xl"
          onClick={onProcessStart}
          className={styles.submit}>
          Top up from Wallet 🚀
        </Button>
      </div>
    </div>
  )
}
