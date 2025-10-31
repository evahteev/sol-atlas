'use client'

import {
  DialogHTMLAttributes,
  FC,
  MouseEventHandler,
  ReactNode,
  useCallback,
  useEffect,
  useRef,
} from 'react'

import clsx from 'clsx'
import { createPortal } from 'react-dom'

import IconClose from '@/images/icons/close.svg'

import Caption from '../Caption'
import Show from '../Show'

import styles from './Dialog.module.scss'

export type DialogProps = DialogHTMLAttributes<HTMLDialogElement> & {
  type?: 'dialog' | 'drawer'
  variant?: 'light' | 'dark'
  caption?: ReactNode
  subtitle?: ReactNode
  isOpen?: boolean
  onOpen?: () => void
  onClose?: (value?: unknown) => void
  isModal?: boolean
  isMaximized?: boolean
}

export const Dialog: FC<DialogProps> = ({
  type = 'dialog',
  variant = 'light',
  caption,
  subtitle,
  children,
  className,
  isOpen,
  onOpen,
  onClose,
  isModal,
  isMaximized,
  ...props
}) => {
  const refDialog = useRef<HTMLDialogElement>(null)

  const handleClickAway: MouseEventHandler<HTMLDialogElement> = (e) => {
    if (e.target === refDialog.current && !isModal) {
      handleClose()
      props?.onClick?.(e)
    }
  }

  const handleOpen = useCallback(() => {
    onOpen?.()
    if (!refDialog.current?.open) {
      refDialog.current?.[isModal ? 'showModal' : 'show']()
    }
  }, [onOpen, refDialog, isModal])

  const handleClose = useCallback(() => {
    onClose?.()
    if (refDialog.current?.open) {
      refDialog.current?.close()
    }
  }, [refDialog, onClose])

  useEffect(() => {
    if (!refDialog?.current) {
      return
    }

    if (isOpen) {
      handleOpen()
    } else {
      handleClose()
    }
  }, [isOpen, handleOpen, handleClose, refDialog])

  if (!isOpen || typeof window === 'undefined' || !document?.body) {
    return null
  }

  return createPortal(
    <dialog
      {...props}
      onClick={handleClickAway}
      className={clsx(styles.wrapper, styles[type], {
        [styles.modal]: styles.modal && isModal,
        [styles.open]: styles.open && isOpen,
      })}
      ref={refDialog}>
      <Show if={isOpen}>
        <div
          className={clsx(
            styles.container,
            styles[type],
            styles[variant],
            {
              [styles.maximized]: styles.maximized && isMaximized,
            },
            className
          )}>
          <Show if={onClose}>
            <button className={styles.close} onClick={handleClose}>
              <IconClose className={styles.closeIcon} />
            </button>
          </Show>

          <Show if={caption || subtitle}>
            <div className={styles.header}>
              <Show if={caption}>
                <Caption variant="body" size="lg" className={styles.title}>
                  {caption}
                </Caption>
              </Show>{' '}
              <Show if={subtitle}>
                <span className={styles.subtitle}>{subtitle}</span>
              </Show>
            </div>
          </Show>

          <div className={styles.body}>{children}</div>
        </div>
      </Show>
    </dialog>,
    document?.body
  )
}
