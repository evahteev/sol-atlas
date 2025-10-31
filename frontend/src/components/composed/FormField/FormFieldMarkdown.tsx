'use client'

import dynamic from 'next/dynamic'

import { DetailedHTMLProps, FC, ReactNode, Suspense, TextareaHTMLAttributes, useState } from 'react'

import clsx from 'clsx'

import Loader from '@/components/atoms/Loader'

import { FormFieldInputSize } from './FormField'
import { getFieldInputableWrapper } from './helpers'

import styles from './FormField.module.scss'

const MarkdownEditor = dynamic(() => import('../MarkdownEditor'), { ssr: false })

type FormFieldTextareaProps = DetailedHTMLProps<
  TextareaHTMLAttributes<HTMLTextAreaElement>,
  HTMLTextAreaElement
>

export type FormFieldMarkdownProps = {
  caption?: ReactNode
  tooltip?: string
  size?: FormFieldInputSize
  children?: ReactNode
} & (Omit<FormFieldTextareaProps, 'size' | 'value' | 'prefix' | 'suffix' | 'multiple'> & {
  defaultValue?: string
  onValueChange?: (value: string) => void
})
export const FormFieldMarkdown: FC<FormFieldMarkdownProps> = (props) => {
  const { caption, className, tooltip, children, defaultValue, ...rest } = props

  const [currentValue, setCurrentValue] = useState(defaultValue || '')
  const handleChange = (val: string) => {
    setCurrentValue(val)
  }

  return getFieldInputableWrapper('div', {
    className,
    caption,
    tooltip,
    type: 'markdown',
    field: (
      <>
        <Suspense fallback={<Loader className={styles.loader} />}>
          <MarkdownEditor
            markdown={`${defaultValue || ''}`}
            className={clsx(className, styles.editor)}
            classNames={{ toolbar: styles.editorToolbar }}
            contentEditableClassName={clsx(
              styles.input,
              styles.markdown,
              styles[props.size || 'lg'],
              styles.editorContent
            )}
            onChange={handleChange}
            placeholder={props.placeholder || ' '}
          />
        </Suspense>
        <textarea
          {...rest}
          value={currentValue}
          className={clsx(
            styles.input,
            styles.textarea,
            styles[props.size || 'lg'],
            styles.editorAssistant
          )}
          disabled={props.disabled}
          onChange={(e) => {
            props.onChange?.(e)
            props.onValueChange?.(e.target.value)
          }}
          placeholder={props.placeholder || ' '}
        />
      </>
    ),
    children,
  })
}
