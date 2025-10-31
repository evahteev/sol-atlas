'use client'

import { DetailedHTMLProps, FC, HTMLAttributes, ReactNode, useEffect } from 'react'

import { Placement, autoUpdate, flip, shift, size, useFloating } from '@floating-ui/react-dom'
import clsx from 'clsx'
import { useForkRef } from 'rooks'

import Portal from '@/components/atoms/Portal'

import Show from '../Show'

import styles from './DropdownContent.module.scss'

type DropdownContentProps = DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement> & {
  className?: string
  element: HTMLElement | null
  content?: ReactNode
  onClose?: () => void
  isOpen?: boolean
  placement?: Placement
}

const DropdownContent: FC<DropdownContentProps> = ({
  element,
  className,
  children,
  content,
  onClose,
  ref,
  isOpen,
  placement,
  ...rest
}) => {
  const { floatingStyles, refs } = useFloating({
    transform: false,
    middleware: [
      shift(),
      flip((state) => {
        const placement = state.placement.split('-')
        const isCenter =
          state.rects.floating.width <= state.elements.reference.getBoundingClientRect().width

        state.elements.floating.setAttribute(
          'data-placement',
          isCenter ? placement[0] : state.placement
        )

        return {}
      }),
      size({
        apply: ({ availableHeight, rects, elements }) => {
          elements.floating.style.setProperty('--_dce-space', `${availableHeight || 0}px`)
          elements.floating.style.setProperty('--_dce-width', `${rects.reference.width || 0}px`)
        },
      }),
    ],
    whileElementsMounted: autoUpdate,
    elements: {
      reference: element,
    },
    placement: placement ?? 'bottom-start',
    strategy: 'fixed',
    open: !!isOpen,
  })

  const mergeRef = useForkRef<HTMLDivElement>(ref, refs.setFloating)

  const handleClickOutside = (event: Event): void => {
    if (
      !event.target ||
      !(
        element?.contains(event.target as Node) ||
        refs.floating.current?.contains(event.target as Node)
      )
    ) {
      onClose?.()
    }
  }

  useEffect(() => {
    document.addEventListener('mousedown', handleClickOutside)
    document.addEventListener('touchend', handleClickOutside)

    return (): void => {
      document.removeEventListener('mousedown', handleClickOutside)
      document.removeEventListener('touchend', handleClickOutside)
    }
  })

  return (
    <Portal
      {...rest}
      ref={mergeRef}
      className={clsx(styles.container, { [styles.open]: isOpen }, className)}
      style={floatingStyles}>
      <Show if={isOpen}>
        {children}
        {content}
      </Show>
    </Portal>
  )
}

export default DropdownContent
