import { PropsWithChildren } from 'react'

export const Show = (props: PropsWithChildren<{ if: unknown }>) => {
  if (props.if) {
    return props.children
  }

  return null
}
