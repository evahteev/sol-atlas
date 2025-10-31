import { HTMLAttributes } from 'react'

import clsx from 'clsx'

import Button, { ButtonProps } from '@/components/ui/Button'
import Show from '@/components/ui/Show'

import styles from './InfoPanel.module.scss'

type InfoPanelProps = HTMLAttributes<HTMLDivElement> & {
  action?: ButtonProps
}

export function InfoPanel({ children, className, action, ...props }: InfoPanelProps) {
  return (
    <div id="info-panel" className={clsx(styles.container, className)} {...props}>
      <div className={styles.body}>{children}</div>

      <Show if={action}>
        <Button {...action} />
      </Show>
    </div>
  )
}
