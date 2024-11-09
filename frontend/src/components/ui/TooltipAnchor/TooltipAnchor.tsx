import clsx from 'clsx'

import Icon from '@/images/icons/tooltip.svg'

import styles from './TooltipAnchor.module.scss'

type TooltipAnchorProps = {
  text?: string
  className?: string
  target?: string
}

export default function TooltipAnchor({
  text,
  className,
  target = 'app-tooltip',
}: TooltipAnchorProps) {
  if (!text) {
    return null
  }

  return (
    <span
      className={clsx(styles.container, className)}
      data-tooltip-id={target}
      data-tooltip-html={text}>
      <Icon className={styles.icon} />
    </span>
  )
}
