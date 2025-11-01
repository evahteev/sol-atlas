import { AmmModel } from './amm'

export type ChainModel = {
  id: number
  name: string
  description: string
  type: 'evm'
  logo_uri: string | null
  enabled?: boolean
  rpc_url: string
  gas_buffer: number
  balances_wss_request: null
  color: string
  secondary_color: string
  primary_token_address: string
  secondary_token_address: string
  gas_url: string

  native_token: {
    id: string
    address: string
    name: string
    symbols: string[]
    logoURI: (string | null)[]
    decimals: number

    priceUSD?: number
    priceUSDChange24h?: number
    verified: true
  }

  amms: AmmModel[]

  block_explorer: {
    url: string
    logo_uri: string
    display_name: string
    token_path: string
    address_path: string
  }

  // most_liquid_tokens: [Array];
  // block_explorer: [Object];
  // zerox_api: [Object];
  // one_inch_api: [Object];
  // market_order: [Object];
  // limit_order: [Object];
}
