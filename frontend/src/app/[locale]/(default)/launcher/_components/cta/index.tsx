import { DetailedHTMLProps, HTMLAttributes, ReactNode } from 'react'

import clsx from 'clsx'

import Button, { ButtonProps } from '@/components/ui/Button'
import Caption from '@/components/ui/Caption'
import Card from '@/components/ui/Card'

import styles from './cta.module.scss'

export const PageLauncherCTA = ({
  className,
  children,
  caption,
  action,
  ...props
}: DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement> & {
  caption: ReactNode
  action: ButtonProps
}) => {
  return (
    <Card className={clsx(styles.container, className)} {...props}>
      <div className={styles.header}>
        <Caption variant="header" size="lg" className={styles.title}>
          {caption}
        </Caption>
      </div>
      <div className={styles.body}>{children}</div>
      <div className={styles.footer}>
        <Button {...action} />
      </div>
    </Card>
  )
}
