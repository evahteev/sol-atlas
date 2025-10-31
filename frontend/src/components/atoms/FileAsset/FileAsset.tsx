import { DetailedHTMLProps, FC, HTMLAttributes } from 'react'

import clsx from 'clsx'

import { ButtonSize } from '@/components/ui/Button'
import Show from '@/components/ui/Show'
import IconUnknown from '@/images/emoji/hmm.svg'
import IconError from '@/images/icons/close.svg'

import ImageFallback from '../ImageFallback'
import Loader from '../Loader'

import styles from './FileAsset.module.scss'

type FileAsset = DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement> & {
  className?: string
  isLoading?: boolean
  isPending?: boolean
  isError?: boolean
  file: {
    name: string
    size: number
    type: string
  }
  size?: ButtonSize
  image?: string | null
}

export const FileAsset: FC<FileAsset> = ({
  className,
  size = 'lg',
  file,
  image = null,
  isLoading = false,
  isPending = false,
  isError = false,
  ...props
}) => {
  const [typeDomain, typeEntity] = (file.type || '').toLowerCase().split('/')
  const fileName = file.name?.split('/').pop()
  const name = fileName?.split('.').shift() || '?'
  const ext = file.name?.split('.').pop()
  const extLower = ext?.toLowerCase()

  return (
    <div
      {...props}
      className={clsx(styles.container, className, styles[size], {
        [styles.loading]: isLoading,
        [styles.pending]: isPending,
        [styles.error]: isError,
      })}>
      <span
        className={styles.illustration}
        data-domain={typeDomain}
        data-type={typeEntity || extLower}
        data-ext={extLower}>
        <Show if={image !== null}>
          <ImageFallback
            src={image || ''}
            fallback={<IconUnknown />}
            className={styles.image}
            title={`${name}.${ext}`}
          />
        </Show>
        <Show if={isLoading || isPending}>
          <Loader className={styles.loader} isActive={false} />
        </Show>
        <Show if={isError}>
          <IconError className={styles.icon} />
        </Show>
      </span>{' '}
      {/* <span className={styles.body}>
        <span className={styles.caption}>
          <span className={styles.name}>{name}</span>
          {ext ? <span className={styles.ext}>.{ext}</span> : null}
        </span>
      </span>{' '}
      <Show if={file.size}>
        <span className={styles.footer}>
          <span className={styles.size}>{formatFileSize(file.size || 0)}</span>
        </span>
      </Show> */}
    </div>
  )
}
