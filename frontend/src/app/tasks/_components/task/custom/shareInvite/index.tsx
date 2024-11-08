'use client'

import Image from 'next/image'

import { FC, useCallback, useEffect, useState } from 'react'

import { shareURL } from '@telegram-apps/sdk-react'
import clsx from 'clsx'
import { get } from 'lodash'
import QRCode from 'qrcode'

import Loader from '@/components/atoms/Loader'
import { Button, Caption, Show } from '@/components/ui'
import { tGuru } from '@/config/wagmi'
import IconCopy from '@/images/icons/copy.svg'
import { trackButtonClick } from '@/utils/analytics'

import { TaskFormCustomProps } from '../../TaskForm'

import styles from './shareInvite.module.scss'

const unit = process.env.NEXT_PUBLIC_APP_CURRENCY ?? tGuru.nativeCurrency.symbol

const TaskFormCustomShareInvite: FC<TaskFormCustomProps> = ({ title, variables, isLoading }) => {
  const [qrCode, setQrCode] = useState<string | null>()

  const inviteLink = get(variables ?? {}, 'text_invite_link')?.value as string

  const handleClickCopy = useCallback(() => {
    trackButtonClick('Button', 'Click', 'Copy link Button')
    if (inviteLink) {
      navigator.clipboard.writeText(inviteLink)
    }
  }, [inviteLink])

  const handleClickShare = useCallback(() => {
    trackButtonClick('Button', 'Click', 'Share with friends Button')
    if (inviteLink) {
      shareURL(inviteLink, `Check the ${process.env.NEXT_PUBLIC_APP_NAME} App!`)
    }
  }, [inviteLink])

  useEffect(() => {
    if (!inviteLink) {
      return
    }

    QRCode.toDataURL(inviteLink ?? '', { type: 'image/jpeg', margin: 1 })
      .then((res) => {
        setQrCode(res)
      })
      .catch((e) => {
        setQrCode(null)
        console.error(e)
      })
  }, [inviteLink])

  if (isLoading) {
    return <Loader className={styles.loader} />
  }

  return (
    <div className={styles.container}>
      <Show if={qrCode}>
        <Image
          src={qrCode ?? ''}
          alt="Share Link QR Code"
          className={styles.illustration}
          width={320}
          height={320}
        />
      </Show>
      <Show if={!qrCode}>
        <span className={clsx(styles.illustration, styles.loading)} />
      </Show>

      <div className={styles.header}>
        <Caption variant="header" size="lg">
          {title}
        </Caption>
      </div>
      <div className={styles.body}>
        <Caption variant="numbers" size="xl" className={styles.value} decorated="fire">
          +5%
        </Caption>
        <div className={styles.description}>
          of your friend&apos;s initial {unit} when they join with your link!
        </div>
        <Button
          caption="Copy link"
          icon={<IconCopy />}
          size="sm"
          onClick={handleClickCopy}
          className={styles.copy}
          isDisabled={!inviteLink}
        />
      </div>
      <div className={styles.footer}>
        <Button
          isBlock
          variant="primary"
          size="xl"
          onClick={handleClickShare}
          className={styles.submit}>
          Share with Friends
        </Button>
      </div>
    </div>
  )
}

export default TaskFormCustomShareInvite
