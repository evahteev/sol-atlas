import React, { DetailedHTMLProps, FC, HTMLAttributes, useEffect, useRef } from 'react'

import clsx from 'clsx'
import { createPortal } from 'react-dom'

import { useDidMount } from '@/hooks/useDidMount'

import styles from './Portal.module.scss'

export const Portal: FC<DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement>> = ({
  children,
  className,
  ...props
}) => {
  const isMounted = useDidMount()
  const containerRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    containerRef.current = document?.body || document?.documentElement
  }, [])

  if (!isMounted || !containerRef.current) {
    return null
  }

  return createPortal(
    <div {...props} className={clsx(styles.container, className)}>
      {children}
    </div>,
    containerRef.current
  )
}
