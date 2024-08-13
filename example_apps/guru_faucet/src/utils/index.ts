// @ts-expect-error https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/BigInt#use_within_json
BigInt.prototype.toJSON = function () {
  return { $bigint: this.toString() }
}

export function isTypeObject(value: unknown) {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
}

export const getShortAddress = (address?: string, count = 4): string => {
  const charCount = Math.max(count, 4)

  const regexp = new RegExp(`(0x)([0-9a-f]{${charCount - 1}})(.+)([0-9a-f]{${charCount}})`, 'i')

  const result = `${address}`.replace(regexp, '$1$2…$4')
  return result
}

export const getAsArray = <T>(value?: T | T[]): T[] =>
  value ? (Array.isArray(value) ? value : [value]) : []

export const getTokenSymbolsString = (symbols: string | string[]) => {
  const symbolsArr = getAsArray(symbols) ?? []
  return symbolsArr?.map(removeUnprintable).join('/') ?? ''
}

export function removeUnprintable(str?: string) {
  if (!str || !hasUnprintable(str)) {
    return str
  }

  const array = []
  for (let i = 0; i < str.length; ++i) {
    const charCode = str.charCodeAt(i)
    if (!isUnprintable(charCode)) {
      array.push(charCode)
    }
  }
  return String.fromCharCode(...array)
}

function hasUnprintable(str?: string) {
  if (!str) {
    return false
  }

  for (let i = 0; i < str.length; ++i) {
    if (isUnprintable(str.charCodeAt(i))) {
      return true
    }
  }
  return false
}

function isUnprintable(charCode: number) {
  return charCode !== 9 && charCode !== 10 && (charCode < 32 || charCode === 65279)
}
