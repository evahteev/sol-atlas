'use client'

import { DetailedHTMLProps, FC, InputHTMLAttributes, ReactNode } from 'react'

import clsx from 'clsx'
import omit from 'lodash/omit'

import { FormFieldInputSize } from './FormField'
import { getFieldInputableWrapper } from './helpers'

import styles from './FormField.module.scss'

type FormFieldInputProps = DetailedHTMLProps<
  InputHTMLAttributes<HTMLInputElement>,
  HTMLInputElement
>

export type FormFieldFileProps = {
  caption?: ReactNode
  tooltip?: string
  className?: string
  id?: string
  isPending?: boolean
  isDisabled?: boolean
  size?: FormFieldInputSize
  children?: ReactNode
} & (Omit<FormFieldInputProps, 'size' | 'value' | 'prefix' | 'suffix' | 'multiple'> & {
  type?: 'file'
  multiple?: boolean
  onValueChange?: (value: string[]) => void
})

export const FormFieldFile: FC<FormFieldFileProps> = (props) => {
  const { caption, className, isDisabled, isPending, tooltip, children, ...rest } = props
  const restSafe = omit(rest, ['onValueChange', 'children', 'value', 'defaultValue'])

  const classNameInput = clsx(
    styles.input,
    styles[props.type || 'text'],
    styles[props.size || 'lg'],
    { [styles.pending]: isPending }
  )

  return getFieldInputableWrapper('div', {
    caption,
    className,
    tooltip,
    type: 'file',
    field: (
      <div className={styles.file}>
        <label className={styles.fileBody}>
          <input
            {...(restSafe as FormFieldInputProps)}
            className={styles.fileControl}
            disabled={props.disabled || isDisabled}
            ref={props?.ref}
            type="file"
            multiple={props.multiple}
          />
          <span className={clsx(styles.fileChoose, classNameInput, styles.custom)}>
            Choose file{props.multiple ? 's' : ''}...
          </span>
        </label>

        {children}
      </div>
    ),
  })
}
