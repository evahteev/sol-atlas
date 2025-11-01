import { FC } from 'react'

import clsx from 'clsx'

import { AppNavigationMainMenuCollapse } from './MainMenuCollapse'
import { AppNavigationMainMenuItem, AppNavigationMainMenuItemProps } from './MainMenuItem'

import styles from './MainMenu.module.scss'

type AppNavigationMainMenuProps = {
  className?: string
  items?: AppNavigationMainMenuItemProps[]
}

export const AppNavigationMainMenu: FC<AppNavigationMainMenuProps> = ({ className, items }) => {
  if (!items?.length) {
    return null
  }

  const collapsedItems: AppNavigationMainMenuItemProps[] = items.filter(
    (item) => item.isCollapsable
  )

  return (
    <nav className={clsx(styles.container, className)} id="main-menu">
      <ul className={styles.list}>
        {items.map(({ ...item }, idx) => {
          return <AppNavigationMainMenuItem {...item} className={styles.link} key={idx} />
        })}
      </ul>

      <AppNavigationMainMenuCollapse items={collapsedItems} />
    </nav>
  )
}
