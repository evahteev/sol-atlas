'use client'

import Image from 'next/image'

import { FC, useCallback, useEffect, useState } from 'react'

import clsx from 'clsx'
import get from 'lodash/get'
import { env } from 'next-runtime-env'
import QRCode from 'qrcode'

import Loader from '@/components/atoms/Loader'
import { TaskFormProps } from '@/components/composed/TaskForm/types'
import Button from '@/components/ui/Button'
import Caption from '@/components/ui/Caption'
import { doCopyToClipboard } from '@/components/ui/Copy/utils'
import Show from '@/components/ui/Show'
import IconCopy from '@/images/icons/copy.svg'

import styles from './shareInvite.module.scss'

const TaskFormCustomShareInvite: FC<TaskFormProps> = ({ title, variables, isLoading }) => {
  const [qrCode, setQrCode] = useState<string | null>()

  const inviteLink = get(variables ?? {}, 'text_invite_link')?.value as string

  const handleClickCopy = useCallback(() => {
    if (inviteLink) {
      doCopyToClipboard(inviteLink)
    }
  }, [inviteLink])

  const handleClickShare = useCallback(() => {
    if (!inviteLink) {
      return
    }

    navigator
      .share({
        title: `Check the ${env('NEXT_PUBLIC_APP_NAME')} App!`,
        url: inviteLink,
      })
      .catch((e) => console.error(e))
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
        <Caption variant="numbers" size="xl" className={styles.value}>
          +5%
        </Caption>
        <div className={styles.description}>
          of your friend&apos;s initial balance when they join with your link!
        </div>
        <Button
          caption="Copy link"
          icon={<IconCopy />}
          isOutline
          variant="primary"
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
