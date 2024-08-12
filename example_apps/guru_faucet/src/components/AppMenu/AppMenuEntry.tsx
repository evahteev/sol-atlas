'use client'

import Link from 'next/link'
import { useParams, usePathname, useSearchParams } from 'next/navigation'

import { CSSProperties, FC, ReactNode, useEffect, useMemo, useState } from 'react'

import clsx from 'clsx'
import { useSelect } from 'downshift'
import { useDimensionsRef, useWindowSize } from 'rooks'

import IconRelated from '@/images/icons/chevron-double-down.svg'
import IconEntry from '@/images/icons/chevron-down.svg'

import Show from '../Show'
import { AppMenuItem } from './AppMenu'

import styles from './AppMenuEntry.module.scss'

type AppMenuEntryProps = {
  type?: 'section' | 'action' | 'related'
  className?: string
  title: ReactNode
  items?: AppMenuItem[]
}

export const AppMenuEntry: FC<AppMenuEntryProps> = ({ type, className, title, items }) => {
  const [currentItems, setCurrentItems] = useState(items || [])
  const pathname = usePathname()
  const params = useParams()
  const searchParams = useSearchParams()
  const matchParams = useMemo(
    () => ({ pathname, params, searchParams }),
    [pathname, params, searchParams]
  )

  useEffect(() => {
    setCurrentItems(items || [])
  }, [items])

  const visibleItems = currentItems?.filter((item) => !item?.isHidden)

  const {
    isOpen,
    getToggleButtonProps,
    getMenuProps,
    highlightedIndex,
    selectedItem,
    getItemProps,
  } = useSelect({
    items: visibleItems.filter((item) => !item.isDelimiter),
    selectedItem: visibleItems.find((item) => item.match?.(matchParams)),
  })

  const [refHolder, , elementHolder] = useDimensionsRef()
  const [refDropdown, , elementDropdown] = useDimensionsRef()
  const { innerWidth } = useWindowSize()

  const rectHolder = elementHolder?.getBoundingClientRect() ?? {
    left: 0,
    width: 0,
    height: 0,
    top: 0,
  }
  const rectDropdown = elementDropdown?.getBoundingClientRect() ?? {
    width: 0,
  }
  const shift = Math.min((innerWidth ?? 0) - rectHolder.left - rectDropdown.width, 0)
  const posLeft = Math.max(rectHolder.left + (shift ?? 0), 0)
  const dropdownPositionStyle = {
    '--_left': posLeft,
    '--_top': rectHolder.top + rectHolder.height,
    '--_width': rectHolder?.width,
  } as CSSProperties

  const hasIcons = !!visibleItems?.filter((item) => !!item.icon).length

  let itemIdx = -1

  return (
    <span className={clsx(styles.container, className)} ref={refHolder}>
      <button
        type="button"
        className={clsx(styles.entry, {
          [styles.hasMenu]: !!visibleItems?.length,
          [styles[type || '']]: !!type,
        })}
        {...getToggleButtonProps()}>
        <span className={styles.caption}>{title}</span>
        {!!visibleItems?.length && type !== 'related' && <IconEntry className={styles.indicator} />}
        {type === 'related' && <IconRelated className={styles.indicator} />}
      </button>

      <>
        <div {...getMenuProps({}, { suppressRefError: true })}>
          <div
            className={clsx(styles.dropdown, {
              [styles.open]: isOpen,
            })}
            style={dropdownPositionStyle}
            ref={refDropdown}>
            <div className={styles.list}>
              {visibleItems?.map((item, index) => {
                if (item.isDelimiter) {
                  return (
                    <div key={index} className={clsx(styles.item, styles.delimiter)}>
                      <Show if={hasIcons}>
                        <span />
                      </Show>

                      <span className={styles.topic}>{item.title}</span>
                      <span className={styles.topic}>{item.description}</span>
                    </div>
                  )
                }

                itemIdx++

                const content = (
                  <>
                    <Show if={hasIcons}>
                      <span className={styles.icon}>{item.icon}</span>
                    </Show>

                    <strong className={styles.title}>{item.title}</strong>
                    <span className={styles.description}>{item.description}</span>
                  </>
                )

                const props = {
                  className: clsx(styles.item, {
                    [styles.hasIcon]: hasIcons,
                    [styles.hilite]: highlightedIndex === itemIdx,
                    [styles.selected]: selectedItem?.key && selectedItem?.key === item.key,
                  }),
                  ...getItemProps({ item, index: itemIdx }),
                }

                if (item.url) {
                  return (
                    <Link {...props} {...(item.linkProps ?? {})} key={index} href={item.url}>
                      {content}
                    </Link>
                  )
                }

                return (
                  <span {...props} key={index}>
                    {content}
                  </span>
                )
              })}
            </div>
          </div>
        </div>
      </>
    </span>
  )
}
