import { FC } from 'react'

import clsx from 'clsx'

import { MainMenuItem, MainMenuItemProps } from './MainMenuItem'

import styles from './MainManu.module.scss'

type MainMenuProps = {
  className?: string
  items?: MainMenuItemProps[]
}

export const MainMenu: FC<MainMenuProps> = ({ className, items }) => {
  if (!items?.length) {
    return null
  }

  return (
    <nav className={clsx(styles.container, className)} id="main-menu">
      <ul className={styles.list}>
        {items.map((item, idx) => {
          return (
            <li key={idx} className={styles.item}>
              <MainMenuItem {...item} className={styles.link} />
            </li>
          )
        })}
      </ul>
    </nav>
  )
}
