'use client'

import {
  DetailedHTMLProps,
  FC,
  HTMLAttributes,
  InputHTMLAttributes,
  PropsWithChildren,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react'

import clsx from 'clsx'
import omit from 'lodash/omit'

import Caption from '@/components/ui/Caption'
import Show from '@/components/ui/Show'
import TooltipAnchor from '@/components/ui/TooltipAnchor'
import IconSelect from '@/images/icons/chevron-down.svg'
import IconSearch from '@/images/icons/search.svg'

import { FormFieldFile } from './FormFieldFile'
import { FormFieldMarkdown } from './FormFieldMarkdown'
import { FormFieldTextarea } from './FormFieldTextarea'
import { getFieldInputableWrapper } from './helpers'

import styles from './FormField.module.scss'

type FormFieldInputTypeNumber = 'number'
type FormFieldInputTypeText =
  | 'text'
  | 'password'
  | 'search'
  | 'date'
  | 'datetime'
  | 'time'
  | 'color'
  | 'email'
  | 'url'
  | 'tel'
  | 'range'
type FormFieldInputType = FormFieldInputTypeNumber | FormFieldInputTypeText | 'file' | never
export type FormFieldInputSize = 'xxs' | 'xs' | 'sm' | 'md' | 'lg' | 'xl' | 'xxl'
type FormFieldSelectOptionProps = { value?: string | number; label: ReactNode }

type FormFieldInputProps = DetailedHTMLProps<
  InputHTMLAttributes<HTMLInputElement>,
  HTMLInputElement
>
type FormFieldTextareaProps = DetailedHTMLProps<
  TextareaHTMLAttributes<HTMLTextAreaElement>,
  HTMLTextAreaElement
>
type FormFieldSelectProps = DetailedHTMLProps<
  SelectHTMLAttributes<HTMLSelectElement>,
  HTMLSelectElement
>
type FormFieldDisplayProps = DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement>

export type FormFieldTarget = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement | null

export type FormFieldProps = {
  caption?: ReactNode
  tooltip?: string
  className?: string
  id?: string
  isPending?: boolean
  isDisabled?: boolean
  indicator?: ReactNode
  size?: FormFieldInputSize
  prefix?: ReactNode
  suffix?: ReactNode
} & (
  | (Omit<FormFieldInputProps, 'size' | 'value' | 'prefix' | 'suffix' | 'multiple'> & {
      type?: FormFieldInputType
      value?: string
    } & (
        | {
            type: 'file'
            multiple?: boolean
            accept?: string
            onValueChange?: (value: File[] | string[]) => void
          }
        | {
            type: FormFieldInputTypeNumber
            value?: number | string
            onValueChange?: (value: number) => void
          }
        | {
            type: FormFieldInputTypeText
            value?: string
            onValueChange?: (value: string) => void
          }
        | {
            type?: never
            value?: string
            onValueChange?: (value: string) => void
          }
      ))
  | (Omit<FormFieldTextareaProps, 'size' | 'value'> & {
      type: 'textarea' | 'markdown'
      value?: string
      onValueChange?: (value: string) => void
    })
  | (Omit<FormFieldInputProps, 'size' | 'value'> & {
      type: 'checkbox' | 'radio' | 'switch'
      value?: string
      defaultChecked?: boolean
      onValueChange?: (value: boolean) => void
    })
  | (Omit<SelectHTMLAttributes<HTMLSelectElement>, 'size' | 'value'> & {
      type: 'select'
      value?: string
      options?: FormFieldSelectOptionProps[]
      placeholder?: string
      onValueChange?: (value: string) => void
    })
  | (FormFieldDisplayProps &
      PropsWithChildren<{
        type: 'display' | 'custom'
        value?: ReactNode
      }>)
)

export const FormField: FC<FormFieldProps> = (props) => {
  let field = null

  const { indicator, caption, className, isDisabled, isPending, tooltip, ...rest } = props
  const restWithNoOnValueChange = omit(rest, 'onValueChange')

  if (props.type === 'checkbox' || props.type === 'radio' || props.type === 'switch') {
    const { defaultChecked, ...restWithoutOnValueChange } = rest
    const restWithNoOnValueChangeForCheckbox = omit(restWithoutOnValueChange, 'onValueChange')

    return (
      <label
        className={clsx(
          styles.container,
          props.type === 'switch' ? styles.switchable : styles.checkable,
          className
        )}>
        <input
          {...(restWithNoOnValueChangeForCheckbox as FormFieldInputProps)}
          defaultChecked={defaultChecked}
          onChange={(e) => {
            props?.onValueChange?.(!!e.target.checked)
            props?.onChange?.(e)
          }}
          disabled={props.disabled || isDisabled}
          className={clsx(
            styles.control,
            styles[props.type],
            { [styles.pending]: isPending },
            props.className
          )}
          type={props.type === 'switch' ? 'checkbox' : props.type}
        />
        <Caption size="sm" className={styles.caption}>
          {caption}
          <Show if={tooltip}>
            <TooltipAnchor text={tooltip} />
          </Show>
        </Caption>{' '}
      </label>
    )
  }

  const classNameInput = clsx(
    styles.input,
    styles[props.type || 'text'],
    styles[props.size || 'lg'],
    { [styles.pending]: isPending }
  )

  if (props.type === 'display' || props.type === 'custom') {
    return (
      <div
        className={clsx(styles.container, styles.inputable, className, {
          [styles.empty]: !(props.value ?? props.children),
        })}
        {...(rest as FormFieldDisplayProps)}>
        {!!caption && (
          <span className={styles.header}>
            <Caption size="sm" className={styles.caption}>
              {caption}
            </Caption>{' '}
            <Show if={tooltip}>
              <TooltipAnchor text={tooltip} />
            </Show>
          </span>
        )}
        <span className={styles.body}>
          <Caption size="sm" className={clsx(classNameInput, { [styles.disabled]: isDisabled })}>
            {props.value ?? props.children}
          </Caption>
        </span>
      </div>
    )
  }

  const commonProps = {
    className: clsx(classNameInput, {
      [styles.markdown]: styles.markdown && props.type === 'markdown',
    }),
  }

  if (props.type === 'file') {
    return <FormFieldFile {...props} />
  }

  if (props.type === 'markdown') {
    return (
      <FormFieldMarkdown {...props} defaultValue={`${props.value || props.defaultValue || ''}`} />
    )
  }

  if (
    !props.type ||
    props.type === 'text' ||
    props.type === 'password' ||
    props.type === 'number' ||
    props.type === 'date' ||
    props.type === 'datetime' ||
    props.type === 'time' ||
    props.type === 'color' ||
    props.type === 'search' ||
    props.type === 'url' ||
    props.type === 'email' ||
    props.type === 'tel' ||
    props.type === 'range'
  ) {
    field = (
      <input
        inputMode={props.type === 'number' ? 'numeric' : 'text'}
        {...(restWithNoOnValueChange as FormFieldInputProps)}
        {...commonProps}
        onChange={(e) => {
          props.onChange?.(e)
          if (props.type === 'number') {
            props?.onValueChange?.(parseFloat(e.target.value))
          } else {
            props?.onValueChange?.(e.target.value)
          }
        }}
        disabled={props.disabled || isDisabled}
        ref={props?.ref}
        placeholder={props.placeholder || ' '}
        type={props.type ?? 'text'}
      />
    )
  }

  if (props.type === 'textarea') {
    field = (
      <FormFieldTextarea
        {...(restWithNoOnValueChange as FormFieldTextareaProps)}
        {...commonProps}
        disabled={props.disabled || isDisabled}
        onChange={(e) => {
          const el = e.target
          props?.onValueChange?.(el.value)
          props.onChange?.(e)
        }}
        ref={props?.ref}
        placeholder={props.placeholder || ' '}
      />
    )
  }

  if (props.type === 'select') {
    field = (
      <>
        <select
          {...(omit(restWithNoOnValueChange, 'options') as FormFieldSelectProps)}
          {...commonProps}
          onChange={(e) => {
            props.onChange?.(e)
            props?.onValueChange?.(e.target.value)
          }}
          disabled={props.disabled || isDisabled}>
          {props.options?.map((option, idx) => (
            <option key={idx} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>

        <span className={styles.indicator}>
          <IconSelect className={styles.icon} />
        </span>
      </>
    )
  }

  return getFieldInputableWrapper('label', {
    caption,
    className: clsx(styles.container, styles.inputable, styles[props.type ?? ''], className),
    tooltip,
    type: props.type,
    field: (
      <>
        <Show if={props.prefix}>
          <span className={styles.prefix}>{props.prefix}</span>
        </Show>

        <Show if={!indicator && props.type === 'search'}>
          <span className={styles.indicator}>
            <IconSearch className={styles.icon} />
          </span>
        </Show>

        {field}

        <Show if={indicator}>
          <span className={styles.indicator}>{indicator}</span>
        </Show>

        <Show if={props.suffix}>
          <span className={styles.suffix}>{props.suffix}</span>
        </Show>
      </>
    ),
    children: props.children,
  })
}
