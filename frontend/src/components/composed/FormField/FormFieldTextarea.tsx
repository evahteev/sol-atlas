'use client'

import { ChangeEventHandler, DetailedHTMLProps, FC, TextareaHTMLAttributes } from 'react'

export const FormFieldTextarea: FC<
  DetailedHTMLProps<TextareaHTMLAttributes<HTMLTextAreaElement>, HTMLTextAreaElement> & {
    onValueChange?: (value: string) => void
  }
> = (props) => {
  const handleOnChange: ChangeEventHandler<HTMLTextAreaElement> = (
    e: React.ChangeEvent<HTMLTextAreaElement>
  ) => {
    const el = e.target
    el.style.height = 'auto'
    el.style.minHeight = '0'
    el.style.boxSizing = 'content-box'
    el.style.paddingBlock = '0'
    el.style.height = el.scrollHeight + 'px'
    el.style.minHeight = ''
    el.style.paddingBlock = ''
    el.style.boxSizing = ''

    props.onChange?.(e)
  }

  return (
    <textarea
      {...props}
      disabled={props.disabled}
      onChange={handleOnChange}
      placeholder={props.placeholder || ' '}
    />
  )
}
