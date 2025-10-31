import { UTCDate } from '@date-fns/utc'
import { isAddress } from 'viem'

import { getShortDate } from './dates'
import { FormatNumberOptions, formatNumber } from './numbers'
import { getShortAddress } from './strings'

export const formatAutoDetect = (value: string | number, options?: FormatNumberOptions): string => {
  const valueStr = value?.toString() ?? ''

  if (isAddress(valueStr)) {
    return getShortAddress(valueStr)
  }

  if (!isNaN(+value)) {
    return formatNumber(value as number, options)
  }

  if (!isNaN(new UTCDate(valueStr).getTime())) {
    return getShortDate(value)
  }

  return valueStr
}

export const formatByType = (
  type: string,
  value: string | number,
  options?: FormatNumberOptions
): string => {
  if (['datetime', 'time', 'date'].includes(type)) {
    return getShortDate(value)
  }

  return formatAutoDetect(value, options)
}

export const formatFileSize = (bytes: number, decimals = 2) => {
  if (!bytes) return '0 Bytes'

  const k = 1024
  const dm = decimals < 0 ? 0 : decimals
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB', 'PB']

  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i]
}
