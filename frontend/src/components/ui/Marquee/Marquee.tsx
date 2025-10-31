'use client'

import Link from 'next/link'

import React, {
  CSSProperties,
  FC,
  HTMLAttributes,
  ReactNode,
  useEffect,
  useRef,
  useState,
} from 'react'

import clsx from 'clsx'

import { getAsArray } from '@/utils'

import Show from '../Show'

import styles from './Marquee.module.scss'

export type MarqueeItem = {
  content?: {
    title?: string | ReactNode
    caption?: string | ReactNode
    icon?: ReactNode
  }
  children?: ReactNode
  url?: string
  onClick?: () => void
}

type MarqueeProps = HTMLAttributes<HTMLDivElement> & {
  className?: string
  items?: MarqueeItem | MarqueeItem[]
  children?: ReactNode
  title?: ReactNode
}

export const Marquee: FC<MarqueeProps> = ({ className, items, title, children, ...rest }) => {
  const [isHovered, setIsHovered] = useState(false)
  const refEl = useRef<HTMLDivElement>(null)
  const [rect, setRect] = useState<DOMRect>()

  const handlePageVisible = () => {
    if (document.visibilityState === 'hidden') {
      setIsHovered(false)
      // @ts-expect-error skipping check active element type, because method will be executed if both of them exist
      document.activeElement?.blur?.()
    }
  }

  const handleFocus = (e: FocusEvent) => {
    setIsHovered(e.relatedTarget !== null)
  }

  useEffect(() => {
    const el = refEl.current
    document.addEventListener('visibilitychange', handlePageVisible)
    el?.addEventListener('focusin', handleFocus)

    return () => {
      document.removeEventListener('visibilitychange', handlePageVisible)
      el?.removeEventListener('focusin', handleFocus)
    }
  }, [])

  const itemsArr = getAsArray(items)

  const renderedContent = (
    <>
      <Show if={children}>
        <div className={styles.data}>{children}</div>
      </Show>

      <Show if={itemsArr?.length}>
        <ul className={styles.list}>
          {itemsArr?.map((item, idx) => {
            const content = (
              <>
                {!!item.content && (
                  <>
                    {item.content?.icon}
                    <span className={styles.link}>{item.content.caption}</span>
                  </>
                )}
                {!!item.children && item.children}
              </>
            )

            const result = item?.url ? (
              <Link
                href={item.url}
                target="_blank"
                rel="noreferrer noopener"
                className={styles.ticker}
                onClick={item.onClick}>
                {content}
              </Link>
            ) : (
              <div className={styles.ticker} onClick={item.onClick}>
                {content}
              </div>
            )

            return (
              <li className={styles.item} key={idx}>
                {result}
              </li>
            )
          })}
        </ul>
      </Show>
    </>
  )

  useEffect(() => {
    if (!refEl.current) {
      return
    }

    setRect(refEl.current.getBoundingClientRect())
  }, [items])

  const handleMouseEnter = () => {
    setIsHovered(true)
  }
  const handleMouseLeave = () => {
    setIsHovered(false)
  }

  return (
    <div className={clsx(styles.container, className)} {...rest}>
      {title && <div className={styles.title}>{title}</div>}
      <div
        className={clsx(styles.body, { [styles.hover]: isHovered })}
        onMouseEnter={handleMouseEnter}
        onMouseLeave={handleMouseLeave}
        style={{ '--_content-width': rect?.width } as CSSProperties}>
        <div className={styles.content} ref={refEl}>
          {renderedContent}
        </div>
        <div className={styles.content} aria-hidden="true">
          {renderedContent}
        </div>
      </div>
    </div>
  )
}
