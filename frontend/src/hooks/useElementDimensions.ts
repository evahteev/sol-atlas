import { RefObject, useCallback, useEffect, useRef, useState } from 'react'

export const useElementDimensions = ({
  ref,
  target,
  enabled = true,
}: {
  ref?: RefObject<HTMLElement>
  target?: HTMLElement | null
  enabled?: boolean
}) => {
  const internalRef = useRef<HTMLElement | null>(null)
  const [dimensions, setDimensions] = useState<DOMRect | null>(null)

  const refresh = useCallback(() => {
    const element = target ?? ref?.current ?? internalRef.current
    const domRect = element?.getBoundingClientRect()
    if (domRect) {
      setDimensions(domRect)
    }
  }, [ref, target])

  useEffect(() => {
    if (!enabled) {
      return
    }

    refresh()
    window.addEventListener('resize', refresh)
    window.addEventListener('scroll', refresh, true)
    return () => {
      window.removeEventListener('resize', refresh)
      window.removeEventListener('scroll', refresh, true)
    }
  }, [enabled, refresh])

  return {
    dimensions,
    ref: ref ?? internalRef, // return ref if provided, otherwise internal
    refresh,
  }
}
