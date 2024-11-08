import { DialogHTMLAttributes, FC, ReactNode, useCallback, useEffect, useRef } from 'react'

import { useClickAway } from '@uidotdev/usehooks'
import clsx from 'clsx'
import { createPortal } from 'react-dom'

import IconClose from '@/images/icons/close.svg'

import { Caption } from '../Caption'
import { Show } from '../Show'

import styles from './Dialog.module.scss'

export type DialogProps = DialogHTMLAttributes<HTMLDialogElement> & {
  caption?: ReactNode
  subtitle?: ReactNode
  isOpen?: boolean
  onOpen?: () => void
  onClose?: (value?: unknown) => void
  isModal?: boolean
  isMaximized?: boolean
}

export const Dialog: FC<DialogProps> = ({
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
  const refContent = useClickAway<HTMLDivElement>(() => {
    if (!isModal) {
      handleClose()
    }
  })

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

  if (!isOpen) {
    // return null
  }

  return createPortal(
    <dialog
      {...props}
      className={clsx(
        styles.wrapper,
        {
          [styles.dialog]: styles.dialog && !isModal,
          [styles.modal]: styles.modal && isModal,
          [styles.open]: styles.open && isOpen,
        },
        className
      )}
      ref={refDialog}>
      <Show if={isOpen}>
        <div
          ref={refContent}
          className={clsx(styles.container, {
            [styles.maximized]: styles.maximized && isMaximized,
          })}>
          <button className={styles.close} onClick={handleClose}>
            <IconClose className={styles.closeIcon} />
          </button>

          <Show if={caption || subtitle}>
            <div className={styles.header}>
              <Caption variant="header" size="lg" className={styles.title} strong>
                {caption}
              </Caption>
              <span className={styles.subtitle}>{subtitle}</span>
            </div>
          </Show>

          <div className={styles.body}>{children}</div>
        </div>
      </Show>
    </dialog>,
    document.body
  )
}
