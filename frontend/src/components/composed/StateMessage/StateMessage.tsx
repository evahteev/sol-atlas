import { DetailedHTMLProps, FC, HTMLAttributes, ReactNode } from 'react'

import clsx from 'clsx'
import omit from 'lodash/omit'

import Button, { ButtonProps } from '@/components/ui/Button'
import Show from '@/components/ui/Show'

import IconDanger from './assets/danger.svg'

import styles from './StateMessage.module.scss'

type StateMessageProps = DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement> & {
  caption?: ReactNode
  text?: ReactNode
  actions?: ButtonProps[]
  type?: 'danger'
  icon?: ReactNode
}

export const StateMessage: FC<StateMessageProps> = ({
  caption,
  text,
  actions,
  type = 'danger',
  icon,
  children,
  ...rest
}) => {
  return (
    <div {...omit(rest, ['type', 'icon'])} className={clsx(styles.container, rest.className)}>
      <Show if={caption || icon}>
        <div className={clsx(styles.illustration, styles[type])}>
          <Show if={!icon}>
            <Show if={type === 'danger'}>
              <IconDanger className={styles.icon} />
            </Show>
          </Show>

          {icon}
        </div>

        <Show if={caption}>
          <div className={styles.header}>
            <strong className={styles.title}>{caption}</strong>
          </div>
        </Show>
      </Show>

      <Show if={text || children}>
        <div className={styles.body}>
          {text}

          {children}
        </div>
      </Show>

      <Show if={actions?.length}>
        <div className={styles.footer}>
          <ul className={styles.list}>
            {actions?.map((item, idx) => (
              <li className={styles.item} key={idx}>
                <Button size="sm" {...item} className={clsx(styles.action, item.className)} />
              </li>
            ))}
          </ul>
        </div>
      </Show>
    </div>
  )
}
