'use client'

import { DetailedHTMLProps, FC, ImgHTMLAttributes, ReactNode, useState } from 'react'

import clsx from 'clsx'

import styles from './ImageFallback.module.scss'

type ImageFallbackProps = DetailedHTMLProps<
  ImgHTMLAttributes<HTMLImageElement>,
  HTMLImageElement
> & {
  fallback: ReactNode
}

export const ImageFallback: FC<ImageFallbackProps> = ({
  fallback,
  alt,
  onLoad,
  onError,
  className,
  ...props
}) => {
  const [state, setState] = useState<{ loading: boolean; error: boolean }>({
    loading: false,
    error: false,
  })

  if (state.error || !props.src) {
    return fallback
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      {...props}
      alt={alt || ''}
      className={clsx(className, styles.image, { [styles.loaded]: !state.loading })}
      onLoadStart={() => setState({ loading: true, error: false })}
      onLoad={(e) => {
        setState({ loading: false, error: false })
        onLoad?.(e)
      }}
      onError={(e) => {
        setState({ loading: false, error: true })
        onError?.(e)
      }}
    />
  )
}
