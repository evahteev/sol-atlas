'use client'

import Link from 'next/link'

import { FC } from 'react'

import clsx from 'clsx'

import Dropdown from '@/components/composed/Dropdown'
import Show from '@/components/ui/Show'
import { useDidMount } from '@/hooks/useDidMount'
import { useIsDesktop } from '@/hooks/useIsDesktop'
import IconMore from '@/images/icons/velliip.svg'

import { AppNavigationMainMenuItemProps } from './MainMenuItem'

import styles from './MainMenuCollapse.module.scss'

type AppNavigationMainMenuProps = {
  className?: string
  items?: AppNavigationMainMenuItemProps[]
}

export const AppNavigationMainMenuCollapse: FC<AppNavigationMainMenuProps> = ({
  className,
  items,
}) => {
  const isDesktop = useIsDesktop()
  const isMounted = useDidMount()

  if (!isMounted || !items?.length || isDesktop) {
    return null
  }

  return (
    <Dropdown
      indicator={<IconMore className={styles.indicator} />}
      className={clsx(styles.container, className)}
      placement="top-end">
      <ul className={styles.list}>
        {items.map((item, idx) => (
          <li className={styles.item} key={idx}>
            <Link href={item.href} className={styles.link}>
              <Show if={item.icon}>
                <span className={styles.icon}>{item.icon}</span>
              </Show>
              <span className={styles.caption}>{item.caption}</span>
            </Link>
          </li>
        ))}
      </ul>
    </Dropdown>
  )
}
