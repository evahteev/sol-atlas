import Link from 'next/link'

import {
  AnchorHTMLAttributes,
  ButtonHTMLAttributes,
  DetailedHTMLProps,
  FC,
  HTMLProps,
  PropsWithChildren,
  ReactNode,
} from 'react'

import clsx from 'clsx'
import { omit } from 'lodash'
import { UrlObject } from 'url'

import styles from './Button.module.scss'

export type ButtonSize = 'xxs' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl'
export type ButtonVariant =
  | 'custom'
  | 'default'
  | 'primary'
  | 'secondary'
  | 'success'
  | 'warn'
  | 'danger'
  | 'info'
  | 'prompt'
  | 'tag'
  | 'switch'
  | 'clear'

type ButtonCommonProps = PropsWithChildren<{
  caption?: ReactNode
  icon?: ReactNode
  indicator?: ReactNode
  counter?: number
  isActive?: boolean
  isDisabled?: boolean
  isPending?: boolean
  tooltip?: string
  variant?: ButtonVariant
  isOutline?: boolean

  size?: ButtonSize
  isBlock?: boolean
}>

export type ButtonLinkProps = Omit<
  DetailedHTMLProps<AnchorHTMLAttributes<HTMLAnchorElement>, HTMLAnchorElement>,
  'href'
> & {
  href: string | UrlObject
  scroll?: boolean
} & ButtonCommonProps

export type ButtonButtonProps = DetailedHTMLProps<
  ButtonHTMLAttributes<HTMLButtonElement>,
  HTMLButtonElement
> & {
  href?: never
  type?: 'button' | 'submit' | 'reset'
} & ButtonCommonProps

export type ButtonProps = (
  | Omit<ButtonLinkProps, 'content'>
  | Omit<ButtonButtonProps, 'content' | 'size'>
) &
  ButtonCommonProps

export const Button: FC<ButtonProps> = (props) => {
  const {
    className,
    caption,
    children,
    icon,
    indicator,
    counter,
    isActive,
    isPending,
    isDisabled,
    variant = 'default',
    size = 'sm',
    tooltip,
    isBlock,
    isOutline,
    ...rest
  } = props

  const buttonClassName = clsx(
    styles.button,
    styles[variant],
    styles[size],
    {
      [styles.block]: isBlock,
      [styles.outline]: isOutline,
      [styles.active]: isActive,
      [styles.pending]: isPending,
      [styles.disabled]: isDisabled ?? (typeof props.href === 'undefined' ? props.disabled : false),
    },
    className
  )

  const typeClassName = styles[rest.type ?? '']
  const commonProps = {
    className: clsx(buttonClassName, { [typeClassName]: !!typeClassName }),
    'data-tooltip-content': tooltip ?? undefined,
    'data-tooltip-id': tooltip ? 'app-tooltip' : undefined,
  }

  const buttonContent = (
    <>
      {!!icon && <span className={styles.icon}>{icon}</span>}
      {(caption || children) && <span className={styles.caption}>{caption || children}</span>}
      {!!indicator && <span className={clsx(styles.indicator, styles.icon)}>{indicator}</span>}
      {!!counter && <span className={styles.counter}>{counter}</span>}
    </>
  )

  if (typeof props.href !== 'undefined') {
    if (isDisabled || isPending) {
      return (
        <span {...(omit(rest, 'scroll') as HTMLProps<HTMLSpanElement>)} {...commonProps}>
          {buttonContent}
        </span>
      )
    }

    return (
      <Link
        {...(rest as DetailedHTMLProps<AnchorHTMLAttributes<HTMLAnchorElement>, HTMLAnchorElement>)}
        {...commonProps}
        ref={props.ref}
        scroll={!!props.scroll}
        className={buttonClassName}
        href={props.href}>
        {buttonContent}
      </Link>
    )
  }

  return (
    <button
      {...(rest as DetailedHTMLProps<ButtonHTMLAttributes<HTMLButtonElement>, HTMLButtonElement>)}
      {...commonProps}
      ref={props.ref}
      disabled={
        isDisabled ?? isPending ?? (typeof props.href === 'undefined' ? props.disabled : false)
      }
      type={props.type ?? 'button'}>
      {buttonContent}
    </button>
  )
}
