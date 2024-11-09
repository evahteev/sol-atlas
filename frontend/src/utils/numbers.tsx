export type FormatNumberOptions = {
  leaveTrailingZeroes?: boolean
} & Intl.NumberFormatOptions

export const getFirstSignificantDecimalIndex = (value: number) =>
  (`${value.toLocaleString('en-US', { minimumFractionDigits: 18 })}`
    .split('.')[1]
    ?.match(/^(0+)[^0]/)?.[1].length || 1) + 1

export const formatNumber = (
  value?: bigint | string | number | null,
  options: FormatNumberOptions = {
    leaveTrailingZeroes: false,
  }
): string => {
  if (typeof value === 'undefined' || value === null) {
    return 'N/A'
  }

  const { leaveTrailingZeroes, ...props } = options

  const valueNumber = Number(value)

  const result = Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits:
      value && Math.abs(valueNumber) < 0.01
        ? Math.max(7, getFirstSignificantDecimalIndex(valueNumber)) + 1
        : 2,
    ...props,
  }).format(valueNumber)

  return !leaveTrailingZeroes ? result.replace(/\.0+$/, '') : result
}

export const getNumber = (value?: number | string | null): number => {
  if (!value) {
    return 0
  }

  const parsedVal = parseFloat(`${value}`)

  return isNaN(parsedVal) ? 0 : parsedVal
}
