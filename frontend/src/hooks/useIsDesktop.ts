import { useWindowSize } from 'rooks'

export const useIsDesktop = () => {
  const size = useWindowSize()
  return (size?.innerWidth ?? 0) > 640
}
