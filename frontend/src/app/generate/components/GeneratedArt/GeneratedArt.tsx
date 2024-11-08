'use client'

import Image from 'next/image'

import clsx from 'clsx'

import FormField from '@/components/composed/FormField'
import { Show } from '@/components/ui'
import IconRotate from '@/images/icons/rotate.svg'
import { useArt } from '@/services/flow/hooks/flow'

import GeneratedArtPlaceholder from './GeneratedArtPlaceholder'

import styles from './GeneratedArt.module.scss'

export type GeneratedArtProps = {
  generatedArtId: string
  onRegenerate?: () => void
}

export default function GeneratedArt({ generatedArtId, onRegenerate }: GeneratedArtProps) {
  const { data: generatedArt, isLoading } = useArt(generatedArtId)

  if (isLoading || !generatedArt) {
    return <GeneratedArtPlaceholder />
  }

  return (
    <div className={styles.container}>
      <div className={styles.containerImg}>
        {generatedArt?.img_picture && (
          <Image
            className={clsx(styles.img)}
            src={generatedArt?.img_picture}
            alt={generatedArt?.type}
            width={320}
            height={320}
          />
        )}
        <Show if={onRegenerate && generatedArt}>
          <div className={styles.containerButton}>
            <button className={styles.regenerate} onClick={onRegenerate}>
              <IconRotate className={styles.icon} />
            </button>
          </div>
        </Show>
      </div>
      <div className={styles.containerDetails}>
        <FormField type="display" caption="Original art title" value={generatedArt?.name} />
        <FormField type="display" caption="Description" value={generatedArt?.description} />
      </div>
    </div>
  )
}
