import Link from 'next/link'

import {
  AnchorHTMLAttributes,
  ButtonHTMLAttributes,
  FC,
  HTMLProps,
  PropsWithChildren,
  ReactNode,
} from 'react'

import clsx from 'clsx'
import { UrlObject } from 'url'

import styles from './Button.module.scss'

type ButtonCommonProps = PropsWithChildren<{
  caption?: ReactNode
  icon?: ReactNode
  indicator?: ReactNode
  counter?: number
  isActive?: boolean
  isDisabled?: boolean
  isPending?: boolean
  tooltip?: string
  variant?: 'default' | 'primary' | 'success' | 'warn' | 'danger' | 'info' | 'prompt' | 'clear'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
}>

export type ButtonLinkProps = Omit<AnchorHTMLAttributes<HTMLAnchorElement>, 'href'> & {
  href: string | UrlObject
  scroll?: boolean
}

export type ButtonButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  href?: never
  type?: 'button' | 'submit' | 'reset'
}

export type ButtonProps = (ButtonLinkProps | ButtonButtonProps) & ButtonCommonProps

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
    size = 'md',
    tooltip,
    ...rest
  } = props

  const buttonClassName = clsx(
    styles.container,
    styles[variant],
    styles[size],
    {
      [styles.active]: isActive,
      [styles.pending]: isPending,
      [styles.disabled]: isDisabled ?? (typeof props.href === 'undefined' ? props.disabled : false),
    },
    className
  )

  const commonProps = {
    className: buttonClassName,
    'data-tooltip-content': tooltip ?? undefined,
    'data-tooltip-id': tooltip ? 'app-tooltip' : undefined,
    scroll: undefined,
  }

  const buttonContent = (
    <>
      {!!icon && <span className={styles.icon}>{icon}</span>}
      {(caption || children) && <span className={styles.caption}>{caption || children}</span>}
      {!!indicator && <span className={styles.indicator}>{indicator}</span>}
      {!!counter && <span className={styles.counter}>{counter}</span>}
    </>
  )

  if (typeof props.href !== 'undefined') {
    if (isDisabled || isPending) {
      return (
        <span {...(rest as HTMLProps<HTMLSpanElement>)} {...commonProps}>
          {buttonContent}
        </span>
      )
    }

    return (
      <Link
        {...(rest as HTMLProps<HTMLAnchorElement>)}
        scroll={props.scroll}
        className={buttonClassName}
        href={props.href}>
        {buttonContent}
      </Link>
    )
  } else {
    const typeClassName = styles[rest.type ?? '']

    return (
      <button
        {...(rest as HTMLProps<HTMLButtonElement>)}
        disabled={
          isDisabled ?? isPending ?? (typeof props.href === 'undefined' ? props.disabled : false)
        }
        {...commonProps}
        className={clsx(buttonClassName, { [typeClassName]: !!typeClassName })}
        type={props.type ?? 'button'}>
        {buttonContent}
      </button>
    )
  }

  return null
}
