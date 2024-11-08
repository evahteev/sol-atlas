import { memo } from 'react'

import clsx from 'clsx'

import styles from './Icon.module.scss'

export type IconProps = {
  iconName: string
  className?: string
}
export const Icon = memo(({ iconName, className }: IconProps) => {
  const iconClasses = clsx(styles.container, className)

  return (
    <div className={iconClasses}>
      <div className={styles.image}>
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
          <use href={`/icons/${iconName}.svg#icon`} />
        </svg>
      </div>
    </div>
  )
})

Icon.displayName = 'Icon'
