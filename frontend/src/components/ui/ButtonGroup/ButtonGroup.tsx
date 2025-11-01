import { FC, HTMLAttributes } from 'react'

import clsx from 'clsx'

import Button, { ButtonProps, ButtonSize, ButtonVariant } from '@/components/ui/Button'

import styles from './ButtonGroup.module.scss'

type ButtonGroupProps = HTMLAttributes<HTMLDivElement> & {
  buttons: ButtonProps[]
  size?: ButtonSize
  variant?: ButtonVariant
  isOutline?: boolean
}

export const ButtonGroup: FC<ButtonGroupProps> = ({
  className,
  buttons,
  size,
  variant,
  isOutline,
  ...rest
}) => {
  if (!buttons.length) {
    return null
  }

  return (
    <div className={clsx(styles.container, className)} {...rest}>
      {buttons.map((button, idx) => {
        return (
          <Button
            isOutline={isOutline}
            variant={variant}
            {...button}
            className={clsx(styles.button, button.className)}
            size={size}
            key={idx}
          />
        )
      })}
    </div>
  )
}
