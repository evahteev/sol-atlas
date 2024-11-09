'use client'

import {
  FC,
  InputHTMLAttributes,
  PropsWithChildren,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react'

import clsx from 'clsx'
import { omit } from 'lodash'

import { Caption } from '@/components/ui'

import styles from './FormField.module.scss'

type FormFieldInputType = 'text' | 'number' | 'password'

type FormFieldInputProps = InputHTMLAttributes<HTMLInputElement>
type FormFieldTextareaProps = TextareaHTMLAttributes<HTMLTextAreaElement>
type FormFieldSelectProps = SelectHTMLAttributes<HTMLSelectElement>

type FormFieldSelectOptionProps = { value?: string; label: ReactNode }

export type FormFieldTarget = HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement | null

export type FormFieldProps = PropsWithChildren<{
  caption?: ReactNode
  tooltip?: string
  className?: string
  id?: string
  isPending?: boolean
  isDisabled?: boolean
}> &
  (
    | (FormFieldInputProps & {
        type?: FormFieldInputType
        unit?: ReactNode
        prefix?: ReactNode
        suffix?: ReactNode
      })
    | (FormFieldTextareaProps & { type: 'textarea' })
    | (FormFieldInputProps & { type: 'checkbox' | 'radio' })
    | (FormFieldSelectProps & {
        type: 'select'
        options: FormFieldSelectOptionProps[]
        placeholder?: string
        itemRender?: (item: unknown) => ReactNode
        listItemRender?: (item: unknown) => ReactNode
        itemKey?: (item: unknown, index?: number) => string
      })
    | { type: 'display'; value?: ReactNode }
    | { type: 'file'; caption: string }
  ) & {
    onValueChange?: (target: FormFieldTarget) => void
  }

export const FormField: FC<FormFieldProps> = (props) => {
  let field = null

  const { caption, className, onValueChange, isDisabled, isPending, ...rest } = props

  if (props.type === 'checkbox' || props.type === 'radio') {
    return (
      <label className={clsx(styles.container, styles.checkable, className)}>
        <input
          onChange={(e) => {
            onValueChange?.(e.target.checked ? e.target : null)
          }}
          {...(rest as FormFieldInputProps)}
          disabled={props.disabled || isDisabled}
          className={clsx(
            styles.control,
            styles[props.type],
            { [styles.pending]: isPending },
            props.className
          )}
          type={props.type ?? 'text'}
        />
        <Caption size="sm" className={styles.caption}>
          {caption}
        </Caption>
      </label>
    )
  }

  const classNameInputable = clsx(
    styles.input,
    styles[props.type ?? 'text'],
    { [styles.pending]: isPending },
    props.className
  )

  if (props.type === 'display') {
    return (
      <label className={clsx(styles.container, styles.inputable, className)}>
        {!!caption && (
          <Caption size="sm" className={styles.caption}>
            {caption}
          </Caption>
        )}
        <Caption size="sm" className={classNameInputable}>
          {props.value}
        </Caption>
      </label>
    )
  }

  if (props.type === 'file') {
    return (
      <div className={styles.inputFileContainer}>
        <input
          type="file"
          id="file"
          accept="image/*"
          name="image"
          onChange={(e) => onValueChange?.(e.target)}
          className={styles.inputFile}
        />
        <label htmlFor="file" className={styles.inputFileLabel}>
          {props.caption}
        </label>
      </div>
    )
  }

  const isTextInput =
    !props.type || props.type === 'text' || props.type === 'password' || props.type === 'number'

  const commonProps = {
    disabled: props.disabled || isDisabled,
    className: classNameInputable,
  }

  if (isTextInput) {
    field = (
      <input
        onChange={(e) => {
          onValueChange?.(e.target)
        }}
        {...(rest as FormFieldInputProps)}
        {...commonProps}
        placeholder={props.placeholder || ' '}
        type={props.type ?? 'text'}
      />
    )
  }

  if (props.type === 'textarea') {
    field = (
      <textarea
        onChange={(e) => {
          onValueChange?.(e.target)
        }}
        {...(rest as FormFieldTextareaProps)}
        {...commonProps}
        placeholder={props.placeholder || ' '}
      />
    )
  }

  if (props.type === 'select') {
    field = (
      <select
        onChange={(e) => {
          onValueChange?.(e.target)
        }}
        {...(omit(rest, 'options') as FormFieldSelectProps)}
        {...commonProps}>
        {props.options.map((option, idx) => (
          <option key={idx} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    )
  }

  return (
    <label className={clsx(styles.container, styles.inputable, className)}>
      {!!caption && (
        <Caption size="sm" className={styles.caption}>
          {caption}
        </Caption>
      )}
      {field}
    </label>
  )
}
