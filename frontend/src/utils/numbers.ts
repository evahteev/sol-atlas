export type FormatNumberOptions = {
  keepTrailingZeroes?: boolean
  precisionMode?: boolean
  suffix?: string
  prefix?: string
} & Intl.NumberFormatOptions

export const getFirstSignificantDecimalIndex = (value: number) =>
  (`${value.toLocaleString('en-US', { minimumFractionDigits: 18 })}`
    .split('.')[1]
    ?.match(/^(0+)[^0]/)?.[1].length || 1) + 1

export const formatNumber = (
  value?: bigint | string | number | null,
  options: FormatNumberOptions = {
    keepTrailingZeroes: false,
    precisionMode: false,
  }
): string => {
  if (typeof value === 'undefined' || value === null) {
    return 'N/A'
  }

  const { keepTrailingZeroes, precisionMode, prefix, suffix, ...props } = options

  const valueNumber = Number(value)

  const result = Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits:
      value && (Math.abs(valueNumber) < 1 || precisionMode)
        ? Math.max(7, getFirstSignificantDecimalIndex(valueNumber) + 1)
        : 2,
    ...props,
  }).format(valueNumber)

  return `${prefix || ''}${!keepTrailingZeroes ? result.replace(/\.0+$/, '') : result}${suffix || ''}`
}

export const getNumber = (value?: number | string | null): number => {
  if (!value) {
    return 0
  }

  const parsedVal = parseFloat(`${value}`)

  return isNaN(parsedVal) ? 0 : parsedVal
}

export const getPreviousPriceByDelta = (currentPrice: number, delta: number): number =>
  currentPrice / (1 + delta)

export const getIntegerPart = (value: number): number => ~~value

export const inputNumberParseValue = (
  val?: string | number | null
): { number: number; value: string } => {
  const valParsed = `${val || ''}`.trim().replace(/[^\d.]/g, '')
  const [int, dec = null] = valParsed.split('.')
  const number = Number(`${int || 0}.${dec || 0}`) || 0
  const value = valParsed ? `${formatNumber(`${int || 0}`)}${dec === null ? '' : `.${dec}`}` : ''

  return { number, value }
}
