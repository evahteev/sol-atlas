import { FC } from 'react'

import clsx from 'clsx'

import styles from './AIChatTyping.module.scss'

type AIChatTypingProps = {
  className?: string
}

export const AIChatTyping: FC<AIChatTypingProps> = ({ className }) => {
  return (
    <div className={clsx(styles.container, className)}>
      <i className={styles.dot} />
      <i className={styles.dot} />
      <i className={styles.dot} />
    </div>
  )
}
