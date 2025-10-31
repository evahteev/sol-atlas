export type TransactionModel = {
  type: string
  network: string
  timestamp: number
  transactionType: string
  transactionAddress: string
  tokenAddresses: [string, string]
  symbols: [string, string]
  wallets: [string, string]
  walletsCategories: [string, string]
  amounts: [number, number]
  amountStable: number
  amountNative: number
  amountsStable: [number, number]
  amountsNative: [number, number]
  pricesStable: [number, number]
  pricesNative: [number, number]
  poolAddress: string
  fromAddress: string
  toAddress: string
  lpToken: null
  sender: string
  to: string
}
