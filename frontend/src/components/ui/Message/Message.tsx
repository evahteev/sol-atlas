import { DetailedHTMLProps, FC, HTMLAttributes, ReactNode } from 'react'

import clsx from 'clsx'

import Button, { ButtonProps } from '../Button'
import Caption from '../Caption'
import Show from '../Show'

import styles from './Message.module.scss'

export type MessageType = 'info' | 'danger' | 'warn' | 'success' | 'prompt'

export type MessageProps = DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement> & {
  caption?: ReactNode
  text?: ReactNode
  type?: 'info' | 'danger' | 'warn' | 'success' | 'prompt' | 'display'
  className?: string
  children?: ReactNode
  actions?: ButtonProps[]
}

const Message: FC<MessageProps> = ({
  caption,
  text,
  type = 'display',
  className,
  children,
  dangerouslySetInnerHTML,
  actions,
  ...props
}) => {
  return (
    <div {...props} className={clsx(styles.container, [styles[type]], className)}>
      <Show if={caption}>
        <div className={styles.header}>
          <Caption variant="body" size="lg" className={styles.title}>
            {caption}
          </Caption>
        </div>
      </Show>

      <Show if={dangerouslySetInnerHTML}>
        <div className={styles.body} dangerouslySetInnerHTML={dangerouslySetInnerHTML} />
      </Show>
      <Show if={!dangerouslySetInnerHTML}>
        <div className={styles.body}>{text || children}</div>
      </Show>

      <Show if={actions}>
        <div className={styles.footer}>
          {actions?.map((action, index) => {
            return <Button {...action} key={index} />
          })}
        </div>
      </Show>
    </div>
  )
}

export default Message
