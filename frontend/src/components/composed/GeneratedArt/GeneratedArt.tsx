'use client'

import Image from 'next/image'

import { useCallback } from 'react'

import clsx from 'clsx'
import { env } from 'next-runtime-env'

import FormField from '@/components/composed/FormField'
import Show from '@/components/ui/Show'
import IconRotate from '@/images/icons/rotate.svg'
import IconShare from '@/images/icons/share.svg'
import { useArt } from '@/services/flow/hooks/flow'

import GeneratedArtPlaceholder from './GeneratedArtPlaceholder'

import styles from './GeneratedArt.module.scss'

type GeneratedArtProps = {
  generatedArtId: string
  onRegenerate?: () => void
  isShareable?: boolean
}

export function GeneratedArt({ generatedArtId, onRegenerate, isShareable }: GeneratedArtProps) {
  const { data: generatedArt, isLoading } = useArt(generatedArtId)

  const onShareTelegramHandler = useCallback(() => {
    if (!generatedArt?.id || !generatedArt.img_picture) {
      return
    }
    const inviteLinkText = `
    
Check what I have just generated in ${env('NEXT_PUBLIC_APP_NAME')} App here ${window.location.origin}!`

    navigator
      .share({
        title: generatedArt.name,
        text: inviteLinkText,
        url: generatedArt.img_picture,
      })
      .catch((e) => console.error(e))
  }, [generatedArt?.id, generatedArt?.img_picture, generatedArt?.name])
  if (isLoading || !generatedArt) {
    return <GeneratedArtPlaceholder />
  }

  return (
    <div className={styles.container}>
      <div className={styles.illustration}>
        {generatedArt?.img_picture && (
          <Image
            className={clsx(styles.image)}
            src={generatedArt?.img_picture}
            alt={generatedArt?.type}
            width={320}
            height={320}
          />
        )}
        <Show if={generatedArt && (onRegenerate || isShareable)}>
          <div className={styles.actions}>
            <Show if={onRegenerate}>
              <button className={styles.action} onClick={onRegenerate}>
                <IconRotate className={styles.icon} />
              </button>
            </Show>

            <Show if={isShareable}>
              <button type="button" className={styles.action} onClick={onShareTelegramHandler}>
                <IconShare className={styles.icon} />
              </button>
            </Show>
          </div>
        </Show>
      </div>
      <div className={styles.body}>
        <FormField type="display" caption="Original art title" value={generatedArt?.name} />
        <FormField type="display" caption="Description" value={generatedArt?.description} />
      </div>
    </div>
  )
}
