import { FC } from 'react'

import clsx from 'clsx'

import Button, { ButtonProps } from '@/components/ui/Button'

import styles from './Tabs.module.scss'

type TabsProps = { variant?: 'sections' | 'options'; className?: string; tabs: ButtonProps[] }

export const Tabs: FC<TabsProps> = ({ className, variant = 'sections', tabs }) => {
  return (
    <div className={clsx(styles.container, styles[variant], className)}>
      <nav className={styles.tabs}>
        {
          <ul className={styles.list}>
            {tabs.map((tab, idx) => {
              return (
                <li className={styles.item} key={idx}>
                  <Button
                    {...tab}
                    variant="custom"
                    size="md"
                    className={clsx(styles.tab, tab.className, { [styles.active]: tab.isActive })}
                  />
                </li>
              )
            })}
          </ul>
        }
      </nav>
    </div>
  )
}
