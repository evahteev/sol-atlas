'use client'

import { FC, PropsWithChildren, ReactNode, useEffect, useRef, useState } from 'react'

import { Placement } from '@floating-ui/react-dom'
import clsx from 'clsx'

import Button from '@/components/ui/Button'
import { ButtonButtonProps } from '@/components/ui/Button/Button'
import IconDown from '@/images/icons/chevron-down.svg'

import DropdownContent from '../../ui/DropdownContent/DropdownContent'

import styles from './Dropdown.module.scss'

type DropdownProps = ButtonButtonProps &
  PropsWithChildren<{
    isOpen?: boolean
    onOpen?: () => void
    onClose?: () => void
    content?: ReactNode
    placement?: Placement
  }>

export const Dropdown: FC<DropdownProps> = ({
  children,
  content,
  variant = 'custom',
  className,
  isOpen = false,
  onClose,
  onOpen,
  placement,
  ...props
}) => {
  const [isCurrentOpen, setIsCurrentOpen] = useState<boolean>(isOpen)
  const refToggle = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    setIsCurrentOpen(isOpen)
  }, [isOpen])

  useEffect(() => {
    if (isCurrentOpen) {
      onOpen?.()
    }
    if (!isCurrentOpen) {
      onClose?.()
    }
  }, [isCurrentOpen, onOpen, onClose])

  const handleClick = () => {
    setIsCurrentOpen(!isCurrentOpen)
  }

  const handleClose = () => {
    setIsCurrentOpen(false)
  }

  return (
    <>
      <Button
        variant={variant}
        indicator={
          <IconDown
            className={clsx(styles.indicator, {
              [styles.open]: isCurrentOpen,
            })}
          />
        }
        {...props}
        type="button"
        className={clsx(styles.toggle, className, {
          [styles.open]: isCurrentOpen,
        })}
        onClick={handleClick}
        ref={refToggle}
      />

      <DropdownContent
        isOpen={isCurrentOpen}
        className={styles.dropdown}
        element={refToggle.current}
        onClose={handleClose}
        placement={placement}>
        {content || children}
      </DropdownContent>
    </>
  )
}
