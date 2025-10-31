import { DetailedHTMLProps, FC, HTMLAttributes } from 'react'

import { marked } from 'marked'

export const TaskFormFieldText: FC<
  DetailedHTMLProps<HTMLAttributes<HTMLDivElement>, HTMLDivElement> & { text?: string }
> = ({ text, ...props }) => {
  const parsedMarkup = marked.parse(text ?? '', { async: false }) as string
  return <div {...props} dangerouslySetInnerHTML={{ __html: parsedMarkup }} />
}
