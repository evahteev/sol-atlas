import { FC, ReactNode } from 'react'

import clsx from 'clsx'

import { Caption } from '../Caption'
import { Show } from '../Show'

import styles from './Message.module.scss'

export type MessageType = 'info' | 'danger' | 'warn' | 'success' | 'prompt'

export type MessageProps = {
  caption?: ReactNode
  text?: ReactNode
  type?: 'info' | 'danger' | 'warn' | 'success' | 'prompt' | 'display'
  className?: string
  children?: ReactNode
}

const Message: FC<MessageProps> = ({ caption, text, type = 'info', className, children }) => {
  return (
    <div className={clsx(styles.container, [styles[type]], className)}>
      <Show if={caption}>
        <div className={styles.header}>
          <Caption variant="body" size="md" className={styles.title} strong>
            {caption}
          </Caption>
        </div>
      </Show>
      <div className={styles.body}>{text || children}</div>
    </div>
  )
}

export default Message
