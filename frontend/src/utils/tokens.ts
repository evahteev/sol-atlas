import { getAsArray, removeUnprintable } from '.'

export const getTokenSymbolsString = (symbols: string | string[]) => {
  const symbolsArr = getAsArray(symbols) ?? []
  return symbolsArr?.map(removeUnprintable).join('/') ?? ''
}
