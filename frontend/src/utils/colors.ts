import distinctColors from 'distinct-colors'

export const DEFAULT_COLOR_MAIN = 'var(--color-info)'

export const getDistinctColors = (
  count: number,
  options?: {
    hueMin?: number
    hueMax?: number
    chromaMin?: number
    chromaMax?: number
    lightMin?: number
    lightMax?: number
    quality?: number
    samples?: number
  }
) => {
  return distinctColors({
    hueMin: 0,
    hueMax: 360,
    chromaMin: 25,
    chromaMax: 100,
    lightMin: 25,
    lightMax: 100,
    ...options,
    count,
  })
}
