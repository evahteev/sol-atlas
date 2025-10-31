import { DetailedHTMLProps, FC, HTMLAttributes, ReactNode } from 'react'

import clsx from 'clsx'

import { getAsArray } from '@/utils'

import styles from './Properties.module.scss'

type PropertiesAlign = 'start' | 'center' | 'end' | null

export type PropertiesItemProps = {
  caption?: ReactNode
  value?: ReactNode
  align?: PropertiesAlign | [PropertiesAlign | undefined, PropertiesAlign]
  className?: string
}

export type PropertiesProps = DetailedHTMLProps<
  HTMLAttributes<HTMLUListElement>,
  HTMLUListElement
> & {
  items?: PropertiesItemProps[]
  align?: PropertiesAlign | PropertiesAlign[] | 'justify'
}

export const Properties: FC<PropertiesProps> = ({ className, items, align, ...props }) => {
  if (!items?.length) {
    return null
  }

  const commonAlign: (string | null | undefined)[] = []
  if (align === 'justify') {
    commonAlign.push('start', 'end')
  } else {
    const alignArr = align ? getAsArray(align) : []
    if (alignArr.length === 1) {
      commonAlign.push(undefined, alignArr[0])
    }
    if (alignArr.length === 2) {
      commonAlign.push(alignArr[0], alignArr[1])
    }
  }

  return (
    <ul {...props} className={clsx(styles.container, className)}>
      {items?.map((item, idx) => {
        const localAlign = []
        const alignArr = item.align ? getAsArray(item.align) : []
        if (alignArr.length === 1) {
          localAlign.push(commonAlign[0], commonAlign[1] ?? alignArr[0])
        }
        if (alignArr.length === 2) {
          localAlign.push(commonAlign[0] ?? alignArr[0], commonAlign[1] ?? alignArr[1])
        }

        const alignCaption = styles[localAlign[0] ?? commonAlign[0] ?? '']
        const alignValue = styles[localAlign[1] ?? commonAlign[1] ?? '']

        return (
          <li className={clsx(styles.item, item.className)} key={idx}>
            <strong
              className={clsx(styles.caption, {
                [alignCaption]: !!alignCaption,
              })}>
              {item.caption}
            </strong>
            <div
              className={clsx(styles.value, {
                [alignValue]: !!alignValue,
              })}>
              {item.value}
            </div>
          </li>
        )
      })}
    </ul>
  )
}
