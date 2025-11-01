import { useCallback, useEffect, useRef } from 'react'

export type Destructor = () => void

/**
 * Guaranteed to run once at the client side.
 */
export const useClientOnce = (callback: () => Destructor | void) => {
  const isCalled = useRef(false)
  const stableCallback = useCallback(() => {
    return callback()
  }, [callback])

  useEffect(() => {
    if (typeof window !== 'undefined' && !isCalled.current) {
      isCalled.current = true
      return stableCallback()
    }
  }, [stableCallback])
}
